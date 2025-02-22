from typing import Dict, Any, List, Union
from langgraph.graph import StateGraph, END
import asyncio
from .nodes.output_node import create_output_node, AgentState
from .nodes.feedback_node import create_feedback_node
from .nodes.scenario_node import create_scenario_node
from .nodes.memory_node import create_memory_node
from .nodes.state_node import create_state_node
from .utils.llm_utils import LLMUtils

def create_agent_workflow(
    llm: LLMUtils,
    initial_state: AgentState
) -> StateGraph:
    """Create the agent workflow graph."""
    
    # Create workflow graph
    workflow = StateGraph(AgentState)
    
    # Create nodes
    output_node = create_output_node(llm)
    feedback_node = create_feedback_node(llm)
    scenario_node = create_scenario_node(llm)
    memory_node = create_memory_node(llm)
    state_node = create_state_node(llm)
    
    # Create sequential processing node
    async def process_sequential(state: AgentState) -> AgentState:
        """Process user input sequentially to ensure full context awareness."""
        try:
            # First analyze feedback and scenario
            state = await feedback_node(state)
            state = await scenario_node(state)
            
            # Then update state and memory
            state = await state_node(state)
            state = await memory_node(state)
            
            # Finally generate response with full context
            state = await output_node(state)
            
            return state
        except Exception as e:
            raise Exception(f"Error in sequential processing: {str(e)}")
    
    # Add nodes to graph
    workflow.add_node("process_sequential", process_sequential)
    
    # Define conditional edges
    def should_continue(state: AgentState) -> Union[str, END]:
        """Determine if we should continue or end the conversation."""
        # Check for explicit exit commands
        user_input = state["user_input"].lower()
        if user_input in ['quit', 'exit', 'bye', '종료', '끝']:
            return END
            
        # Check for max failures
        if state.get("response", {}).get("metadata", {}).get("max_failures_reached", False):
            return END
            
        # Check for scenario completion without next scenario
        if state.get("response", {}).get("metadata", {}).get("scenario_changed", False) is False and \
           state.get("response", {}).get("metadata", {}).get("completion_reason") is not None:
            return END
            
        # Continue with next user input
        return END
    
    # Add conditional edge from process_sequential to end
    workflow.add_conditional_edges(
        "process_sequential",
        should_continue,
        {
            END: END
        }
    )
    
    # Set entry point
    workflow.set_entry_point("process_sequential")
    
    # Compile workflow
    return workflow.compile()

async def run_agent(
    workflow: StateGraph,
    user_input: str,
    state: AgentState
) -> Dict[str, Any]:
    """Run the agent workflow with user input."""
    try:
        # Update state with user input
        state["user_input"] = user_input
        state["response"] = None
        
        # Run workflow
        final_state = await workflow.ainvoke(state)
        
        return {
            "response": final_state["response"]["response_text"],
            "metadata": final_state["response"]["metadata"]
        }
    except Exception as e:
        raise Exception(f"Error running agent: {str(e)}") 