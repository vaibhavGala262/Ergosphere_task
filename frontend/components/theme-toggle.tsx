"use client";

import { Moon, SunMedium } from "lucide-react";
import { useEffect, useState } from "react";

export function ThemeToggle() {
  const [dark, setDark] = useState(false);

  useEffect(() => {
    const stored = window.localStorage.getItem("theme");
    const prefersDark = stored ? stored === "dark" : window.matchMedia("(prefers-color-scheme: dark)").matches;
    setDark(prefersDark);
    document.documentElement.classList.toggle("dark", prefersDark);
  }, []);

  const toggle = () => {
    const next = !dark;
    setDark(next);
    document.documentElement.classList.toggle("dark", next);
    window.localStorage.setItem("theme", next ? "dark" : "light");
  };

  return (
    <button
      onClick={toggle}
      className="rounded-full border border-white/15 bg-white/10 px-4 py-2 text-sm text-text transition hover:border-accent/70 hover:text-accent"
      type="button"
    >
      <span className="flex items-center gap-2">
        {dark ? <SunMedium className="h-4 w-4" /> : <Moon className="h-4 w-4" />}
        {dark ? "Light" : "Dark"}
      </span>
    </button>
  );
}
