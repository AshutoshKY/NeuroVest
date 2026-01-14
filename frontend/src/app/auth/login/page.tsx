'use client';

import { useState } from 'react';
import Link from 'next/link';
import { useRouter } from 'next/navigation';
import { motion } from 'framer-motion';
import { useAuthStore } from '@/store/authStore';
import { NeuroVestLogo } from '@/components/NeuroVestLogo';
import { TrendingUp, Lock, Zap, Shield, ArrowRight, CheckCircle2 } from 'lucide-react';

export default function LoginPage() {
  const router = useRouter();
  const { login, isLoading } = useAuthStore();
  const [formData, setFormData] = useState({
    email: '',
    password: ''
  });
  const [error, setError] = useState('');

  const handleSubmit = async (e: React.FormEvent) => {
    e.preventDefault();
    setError('');

    try {
      await login(formData.email, formData.password);
      // Get user from store to check role
      const { user } = useAuthStore.getState();
      const isAdmin = user?.role === 'admin' || user?.role === 'super_admin';
      router.push(isAdmin ? '/admin' : '/dashboard');
    } catch (err: any) {
      const errorMessage = err.message || err.response?.data?.detail || 'Login failed. Please check your credentials.';
      setError(errorMessage);
      console.error('[LOGIN] Error:', errorMessage);
    }
  };

  const features = [
    { icon: TrendingUp, text: 'Technical Analysis' },
    { icon: Shield, text: 'Sentiment Analysis' },
    { icon: Zap, text: 'Price Predictions' }
  ];

  return (
    <div className="min-h-screen bg-gradient-to-br from-slate-950 via-slate-900 to-emerald-950 flex items-center justify-center p-6 relative overflow-hidden">
      {/* Animated background elements */}
      <div className="absolute inset-0 overflow-hidden pointer-events-none">
        <motion.div
          className="absolute top-1/4 -left-1/4 w-96 h-96 bg-emerald-500/10 rounded-full blur-3xl"
          animate={{
            scale: [1, 1.2, 1],
            opacity: [0.3, 0.5, 0.3],
          }}
          transition={{ duration: 8, repeat: Infinity }}
        />
        <motion.div
          className="absolute bottom-1/4 -right-1/4 w-96 h-96 bg-cyan-500/10 rounded-full blur-3xl"
          animate={{
            scale: [1.2, 1, 1.2],
            opacity: [0.5, 0.3, 0.5],
          }}
          transition={{ duration: 8, repeat: Infinity, delay: 1 }}
        />
      </div>

      <div className="w-full max-w-6xl grid lg:grid-cols-2 gap-8 relative z-10">
        {/* Left side - Branding & Features */}
        <motion.div
          initial={{ opacity: 0, x: -20 }}
          animate={{ opacity: 1, x: 0 }}
          transition={{ duration: 0.6 }}
          className="hidden lg:flex flex-col justify-center space-y-8"
        >
          <div>
            <Link href="/" className="inline-block">
              <NeuroVestLogo className="w-12 h-12 mb-6" />
            </Link>
            <motion.h1
              className="text-5xl font-bold text-white mb-4"
              initial={{ opacity: 0, y: 20 }}
              animate={{ opacity: 1, y: 0 }}
              transition={{ delay: 0.2 }}
            >
              Welcome Back to
              <span className="bg-gradient-to-r from-emerald-400 to-cyan-400 bg-clip-text text-transparent"> NeuroVest</span>
            </motion.h1>
            <motion.p
              className="text-xl text-slate-400"
              initial={{ opacity: 0, y: 20 }}
              animate={{ opacity: 1, y: 0 }}
              transition={{ delay: 0.3 }}
            >
              Continue your AI-powered trading journey
            </motion.p>
          </div>

          {/* Features */}
          <div className="space-y-4">
            {features.map((feature, index) => (
              <motion.div
                key={index}
                initial={{ opacity: 0, x: -20 }}
                animate={{ opacity: 1, x: 0 }}
                transition={{ delay: 0.4 + index * 0.1 }}
                className="flex items-center space-x-4 p-4 rounded-xl bg-white/5 backdrop-blur-sm border border-white/10 hover:border-emerald-500/50 transition-colors"
              >
                <div className="p-3 rounded-lg bg-gradient-to-br from-emerald-500/20 to-cyan-500/20">
                  <feature.icon className="w-6 h-6 text-emerald-400" />
                </div>
                <span className="text-slate-200 font-medium">{feature.text}</span>
              </motion.div>
            ))}
          </div>

          {/* Project Info */}
          <motion.div
            className="grid grid-cols-3 gap-4"
            initial={{ opacity: 0, y: 20 }}
            animate={{ opacity: 1, y: 0 }}
            transition={{ delay: 0.7 }}
          >
            <div className="text-center p-4 rounded-xl bg-white/5 backdrop-blur-sm">
              <div className="text-2xl font-bold text-emerald-400">15+</div>
              <div className="text-sm text-slate-400">Indicators</div>
            </div>
            <div className="text-center p-4 rounded-xl bg-white/5 backdrop-blur-sm">
              <div className="text-2xl font-bold text-cyan-400">Real-time</div>
              <div className="text-sm text-slate-400">Market Data</div>
            </div>
            <div className="text-center p-4 rounded-xl bg-white/5 backdrop-blur-sm">
              <div className="text-2xl font-bold text-purple-400">100%</div>
              <div className="text-sm text-slate-400">Open Source</div>
            </div>
          </motion.div>
        </motion.div>

        {/* Right side - Login Form */}
        <motion.div
          initial={{ opacity: 0, x: 20 }}
          animate={{ opacity: 1, x: 0 }}
          transition={{ duration: 0.6 }}
          className="flex items-center justify-center"
        >
          <div className="w-full max-w-md">
            <motion.div
              className="bg-slate-900/80 backdrop-blur-xl border border-emerald-500/20 rounded-3xl p-8 shadow-2xl shadow-emerald-500/10"
              whileHover={{ boxShadow: "0 25px 50px -12px rgba(16, 185, 129, 0.2)" }}
              transition={{ duration: 0.3 }}
            >
              {/* Mobile Logo */}
              <div className="lg:hidden mb-8 text-center">
                <NeuroVestLogo className="w-9 h-9 mx-auto mb-4" />
              </div>

              {/* Header */}
              <div className="text-center mb-8">
                <motion.div
                  initial={{ scale: 0 }}
                  animate={{ scale: 1 }}
                  transition={{ delay: 0.2, type: "spring" }}
                  className="inline-flex items-center justify-center px-4 py-2 rounded-full bg-gradient-to-r from-emerald-500/20 to-cyan-500/20 border border-emerald-500/30 mb-4"
                >
                  <Lock className="w-4 h-4 text-emerald-400 mr-2" />
                  <span className="text-sm font-semibold text-emerald-400">Secure Login</span>
                </motion.div>

                <h2 className="text-3xl font-bold text-white mb-2">Sign in to your account</h2>
                <p className="text-slate-400">Continue your AI-powered trading journey</p>
              </div>

              {/* Error Message */}
              {error && (
                <motion.div
                  initial={{ opacity: 0, y: -10 }}
                  animate={{ opacity: 1, y: 0 }}
                  className="bg-red-500/10 border border-red-500/30 text-red-400 px-4 py-3 rounded-xl mb-6 flex items-start"
                >
                  <span className="text-lg mr-2">⚠️</span>
                  <span className="text-sm">{error}</span>
                </motion.div>
              )}

              {/* Form */}
              <form onSubmit={handleSubmit} className="space-y-5">
                <div>
                  <label className="block text-emerald-400 text-sm font-semibold mb-2">
                    Email Address
                  </label>
                  <motion.input
                    whileFocus={{ scale: 1.01 }}
                    type="email"
                    value={formData.email}
                    onChange={(e) => setFormData({ ...formData, email: e.target.value })}
                    placeholder="trader@example.com"
                    required
                    disabled={isLoading}
                    className="w-full px-4 py-3 bg-slate-800/50 border border-slate-700 rounded-xl text-white placeholder-slate-500 focus:border-emerald-500 focus:ring-2 focus:ring-emerald-500/20 transition-all outline-none disabled:opacity-50"
                  />
                </div>

                <div>
                  <label className="block text-emerald-400 text-sm font-semibold mb-2">
                    Password
                  </label>
                  <motion.input
                    whileFocus={{ scale: 1.01 }}
                    type="password"
                    value={formData.password}
                    onChange={(e) => setFormData({ ...formData, password: e.target.value })}
                    placeholder="••••••••"
                    required
                    disabled={isLoading}
                    className="w-full px-4 py-3 bg-slate-800/50 border border-slate-700 rounded-xl text-white placeholder-slate-500 focus:border-emerald-500 focus:ring-2 focus:ring-emerald-500/20 transition-all outline-none disabled:opacity-50"
                  />
                </div>

                <motion.button
                  whileHover={{ scale: 1.02 }}
                  whileTap={{ scale: 0.98 }}
                  type="submit"
                  disabled={isLoading}
                  className="w-full py-3.5 bg-gradient-to-r from-emerald-500 to-cyan-500 hover:from-emerald-600 hover:to-cyan-600 text-white font-bold rounded-xl shadow-lg shadow-emerald-500/30 disabled:opacity-50 disabled:cursor-not-allowed transition-all flex items-center justify-center group"
                >
                  {isLoading ? (
                    <span>Signing in...</span>
                  ) : (
                    <>
                      <span>Sign In</span>
                      <ArrowRight className="w-5 h-5 ml-2 group-hover:translate-x-1 transition-transform" />
                    </>
                  )}
                </motion.button>
              </form>

              {/* Footer Links */}
              <div className="mt-8 text-center space-y-4">
                <p className="text-slate-400 text-sm">
                  Don't have an account?{' '}
                  <Link href="/auth/signup" className="text-emerald-400 hover:text-emerald-300 font-semibold transition-colors">
                    Create one now
                  </Link>
                </p>

                <Link
                  href="/"
                  className="inline-flex items-center text-slate-500 hover:text-slate-300 text-sm transition-colors"
                >
                  ← Back to Home
                </Link>
              </div>
            </motion.div>

            {/* Trust Badges */}
            <motion.div
              initial={{ opacity: 0, y: 20 }}
              animate={{ opacity: 1, y: 0 }}
              transition={{ delay: 0.8 }}
              className="mt-6 flex items-center justify-center space-x-6 text-xs text-slate-500"
            >
              <div className="flex items-center">
                <CheckCircle2 className="w-4 h-4 text-emerald-500 mr-1" />
                Encrypted Data
              </div>
              <div className="flex items-center">
                <CheckCircle2 className="w-4 h-4 text-emerald-500 mr-1" />
                Educational Tool
              </div>
            </motion.div>
          </div>
        </motion.div>
      </div>
    </div>
  );
}