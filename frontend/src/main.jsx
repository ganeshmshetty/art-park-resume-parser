import React from "react";
import ReactDOM from "react-dom/client";

import App from "./App";
// NOTE: styles.css is imported inside App.jsx

ReactDOM.createRoot(document.getElementById("root")).render(
  <React.StrictMode>
    <App />
  </React.StrictMode>,
);
