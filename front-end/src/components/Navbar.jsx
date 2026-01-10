import { Link } from 'react-router-dom';
import "../index.css";

export default function Navbar() {
  return (
    <nav className="navbar">
      <div className="nav-left">
        <img src="/apple.svg" alt="logo" className="logo-icon" />
        <span className="brand">Violina</span>
      </div>

      <div className="nav-center">
        <Link to="/">Home</Link>
        <Link to="/tuner">Tuner</Link>
      </div>

      <div className="nav-right">
        <span className="icon">👤</span>
        <span className="icon">🛍</span>
      </div>
    </nav>
  );
}

