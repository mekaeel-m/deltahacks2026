import { BrowserRouter as Router, Routes, Route } from "react-router-dom";
import Home from "./pages/Home.jsx";
import BackgroundShader from "./components/BackgroundShader";
import WebcamStream from "./components/WebcamStream.jsx";



export default function App() {
  return (
    <>
      <BackgroundShader />
      <Router>
        <Routes>
          <Route path="/" element={<Home />} />
        </Routes>
      </Router>
    </>
  )
}