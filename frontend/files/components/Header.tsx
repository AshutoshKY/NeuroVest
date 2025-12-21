import { motion } from 'framer-motion';
import { TrendingUp, Menu, X } from 'lucide-react';
import { useState } from 'react';

interface HeaderProps {
  onOpenAuth: (mode: 'login' | 'signup') => void;
}

export function Header({ onOpenAuth }: HeaderProps) {
  const [isMobileMenuOpen, setIsMobileMenuOpen] = useState(false);

  const scrollToSection = (id: string) => {
    const element = document.getElementById(id);
    if (element) {
      element.scrollIntoView({ behavior: 'smooth' });
      setIsMobileMenuOpen(false);
    }
  };

  return (
    <motion.header
      initial={{ y: -100 }}
      animate={{ y: 0 }}
      transition={{ duration: 0.6 }}
      className="fixed top-0 left-0 right-0 z-50 bg-slate-950/80 backdrop-blur-xl border-b border-slate-800"
    >
      <div className="max-w-7xl mx-auto px-4 sm:px-6 lg:px-8">
        <div className="flex items-center justify-between h-16">
          {/* Logo */}
          <motion.div 
            className="flex items-center gap-2 cursor-pointer"
            whileHover={{ scale: 1.05 }}
          >
            <div className="w-10 h-10 bg-gradient-to-br from-emerald-400 to-cyan-500 rounded-lg flex items-center justify-center">
              <TrendingUp className="w-6 h-6 text-slate-950" />
            </div>
            <span className="text-white text-xl">StockAI</span>
          </motion.div>

          {/* Desktop Navigation */}
          <nav className="hidden md:flex items-center gap-8">
            <button onClick={() => scrollToSection('features')} className="text-slate-300 hover:text-white transition-colors">
              Features
            </button>
            <button onClick={() => scrollToSection('pricing')} className="text-slate-300 hover:text-white transition-colors">
              Pricing
            </button>
            <button onClick={() => scrollToSection('docs')} className="text-slate-300 hover:text-white transition-colors">
              Documentation
            </button>
          </nav>

          {/* Desktop Auth Buttons */}
          <div className="hidden md:flex items-center gap-4">
            <motion.button
              whileHover={{ scale: 1.05 }}
              whileTap={{ scale: 0.95 }}
              onClick={() => onOpenAuth('login')}
              className="px-4 py-2 text-slate-300 hover:text-white transition-colors"
            >
              Login
            </motion.button>
            <motion.button
              whileHover={{ scale: 1.05 }}
              whileTap={{ scale: 0.95 }}
              onClick={() => onOpenAuth('signup')}
              className="px-6 py-2 bg-gradient-to-r from-emerald-500 to-cyan-500 text-white rounded-lg hover:shadow-lg hover:shadow-emerald-500/50 transition-shadow"
            >
              Sign Up
            </motion.button>
          </div>

          {/* Mobile Menu Button */}
          <button
            onClick={() => setIsMobileMenuOpen(!isMobileMenuOpen)}
            className="md:hidden text-white"
          >
            {isMobileMenuOpen ? <X className="w-6 h-6" /> : <Menu className="w-6 h-6" />}
          </button>
        </div>

        {/* Mobile Menu */}
        {isMobileMenuOpen && (
          <motion.div
            initial={{ opacity: 0, height: 0 }}
            animate={{ opacity: 1, height: 'auto' }}
            exit={{ opacity: 0, height: 0 }}
            className="md:hidden py-4 border-t border-slate-800"
          >
            <div className="flex flex-col gap-4">
              <button onClick={() => scrollToSection('features')} className="text-slate-300 hover:text-white transition-colors text-left">
                Features
              </button>
              <button onClick={() => scrollToSection('pricing')} className="text-slate-300 hover:text-white transition-colors text-left">
                Pricing
              </button>
              <button onClick={() => scrollToSection('docs')} className="text-slate-300 hover:text-white transition-colors text-left">
                Documentation
              </button>
              <div className="flex flex-col gap-2 pt-2 border-t border-slate-800">
                <button
                  onClick={() => onOpenAuth('login')}
                  className="px-4 py-2 text-slate-300 hover:text-white transition-colors text-left"
                >
                  Login
                </button>
                <button
                  onClick={() => onOpenAuth('signup')}
                  className="px-6 py-2 bg-gradient-to-r from-emerald-500 to-cyan-500 text-white rounded-lg"
                >
                  Sign Up
                </button>
              </div>
            </div>
          </motion.div>
        )}
      </div>
    </motion.header>
  );
}
