import { StrictMode } from "react";
import { createRoot } from "react-dom/client";
import App from "./App";
import { PreferencesProvider } from "./preferences";
import "./styles.css";

createRoot(document.getElementById("root")!).render(
  <StrictMode><PreferencesProvider><App /></PreferencesProvider></StrictMode>,
);
