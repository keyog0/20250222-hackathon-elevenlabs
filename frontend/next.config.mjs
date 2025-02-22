/** @type {import('next').NextConfig} */
const nextConfig = {
  redirects: () => {
    return [
      {
        source: "/",
        destination: "/start",
        permanent: true,
      },
    ];
  },
};

export default nextConfig;
