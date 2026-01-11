import { Link } from 'react-router-dom';
import "../styles/Navbar.css";

export default function Navbar() {
  return (
    <nav className="navbar">
      <div className="nav-left">
        <img src="/violinalogoenhanced.png" alt="Violina logo" className="logo-icon" />
        <span className="brand">Violina</span>
      </div>
      <div className="nav-center">
      </div>
      <div className="nav-right">
        <button className="nav-link" onClick={() => document.getElementById('pose-detection-section')?.scrollIntoView({behavior: 'smooth'})}>Form</button>
        <button className="nav-link" onClick={() => document.getElementById('practice-tools-section')?.scrollIntoView({behavior: 'smooth'})}>Tuner & Metronome</button>
      </div>
    </nav>
  );
}

