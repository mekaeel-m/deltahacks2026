import { Link } from 'react-router-dom';
import "../styles/Navbar.css";

export default function Navbar() {
  return (
    <nav className="navbar">
      <div className="nav-left">
        <img src="/violinalogo.png" alt="Violina logo" className="logo-icon" />
        <span className="brand">Violina</span>
      </div>
      <div className="nav-center">
        <Link to="/">Home</Link>
        <Link to="/tuner">Tuner</Link>
      </div>
    </nav>
  );
}

