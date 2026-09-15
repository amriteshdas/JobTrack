import { BrowserRouter } from "react-router-dom";
import AppRoutes from "./routes/AppRoutes";

// App.jsx is intentionally a thin shell: routing + (later) context
// providers like AuthProvider. Actual pages/components live elsewhere so
// this file stays stable as the app grows.
function App() {
  return (
    <BrowserRouter>
      <AppRoutes />
    </BrowserRouter>
  );
}

export default App;
