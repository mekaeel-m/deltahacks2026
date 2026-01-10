import "../index.css";

export default function Navbar() {
    return (
        <nav>
            <div className="logo">
                <img href="" alt="logo of application"/>
                <span>Music App</span>
            </div>

            <div className="links">
                <Link to="">Home</Link>
                <Link to="">About us</Link>
                <Link to="">Form Detection</Link>
                <Link to="">Tuner</Link>
            </div>
            
        </nav>
    );
}