import { BrowserRouter as Router, Routes, Route } from "react-router-dom";
import Home from "./pages/Home.jsx";
import Tuner from "./pages/Tuner.jsx";
import Cursor from "./components/Cursor.jsx";
import BackgroundShader from "./components/BackgroundShader";



export default function App() {
  return (
    <>
      <BackgroundShader />
      <Cursor />
      <Router>
        <Routes>
          <Route path="/" element={<Home />} />
          <Route path="/tuner" element={<Tuner/>} />
        </Routes>
      </Router>
    </>
  )
}