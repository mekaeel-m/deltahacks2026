import { BrowserRouter as Router, Routes, Route } from "react-router-dom";
import Home from "./pages/Home.jsx";
import Tuner from "./pages/Tuner.jsx";


export default function App() {
  return (
    <>
      <Router>
        <Routes>
          <Route path="/" element={<Home />} />
          <Route path="/tuner" element={<Tuner/>} />
        </Routes>
      </Router>
    </>
  )
}