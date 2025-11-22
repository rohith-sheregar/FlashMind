export default {
  content: [
    "./index.html",
    "./src/**/*.{js,jsx,ts,tsx}",
    "./src/index.css" // REQUIRED for custom animations
  ],
  theme: {
    extend: {
      keyframes: {
        float: {
          "0%": { transform: "translateY(0px) translateX(0px)" },
          "50%": { transform: "translateY(-20px) translateX(10px)" },
          "100%": { transform: "translateY(0px) translateX(0px)" }
        },
      },
      animation: {
        float: "float 6s ease-in-out infinite",
      }
    },
  },
  plugins: [],
}
