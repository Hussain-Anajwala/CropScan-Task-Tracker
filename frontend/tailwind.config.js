/** @type {import('tailwindcss').Config} */
export default {
  content: ["./index.html", "./src/**/*.{js,jsx}"],
  theme: {
    extend: {
      colors: {
        cropscan: {
          leaf: "#3f7d20",
          soil: "#7c4f2d",
          sun: "#f2b84b",
        },
      },
    },
  },
  plugins: [],
};
