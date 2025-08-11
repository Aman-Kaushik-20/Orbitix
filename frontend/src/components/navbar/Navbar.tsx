// src/components/Navbar.tsx
import React from "react";

const Navbar: React.FC = React.memo(() => {
  return (
    <div className="fixed top-6 left-1/2 -translate-x-1/2 z-50">
      <nav className="flex items-center gap-6 px-6 py-2 bg-neutral-900/80 backdrop-blur-md rounded-full shadow-lg border border-neutral-800">
        
        {/* Project Name */}
        <a
          href="/"
          className="text-white font-semibold text-lg flex items-center gap-2"
        >
          <span className="w-6 h-6 bg-white rounded-md" /> {/* Logo placeholder */}
          Orbitix
        </a>

        {/* Empty space between name and button */}
        <div className="flex-1"></div>

        {/* Sign Up Button */}
        <a
          href="/signup"
          className="px-4 py-1 bg-white text-black font-medium rounded-full shadow hover:bg-neutral-200 transition"
        >
          Sign Up →
        </a>
      </nav>
    </div>
  );
});

export default Navbar;
