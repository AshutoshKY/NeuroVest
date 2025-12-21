'use client';

import { useState } from 'react';
import Link from 'next/link';
import { useRouter } from 'next/navigation';
import { motion } from 'framer-motion';
import { useAuthStore } from '@/store/authStore';
import { NeuroVestLogo } from '@/components/NeuroVestLogo';
import { TrendingUp, Shield, Zap, Users, ArrowRight, CheckCircle2, Crown, BarChart3 } from 'lucide-react';

export default function SignupPage() {
  const router = useRouter();
  const { signup, isLoading } = useAuthStore();
  const [formData, setFormData] = useState({
    email: '',
    password: '',
    confirmPassword: ''
  });
  const [error, setError] = useState('');

  const handleSubmit = async (e: React.FormEvent) => {
    e.preventDefault();
    setError('');

    if (formData.password !== formData.confirmPassword) {
      setError('Passwords do not match');
      return;
    }

    if (formData.password.length < 8) {
      setError('Password must be at least 8 characters long');
      return;
    }

    try {
      await signup(formData.email, formData.password, formData.email.split('@')[0]);
      router.push('/dashboard');
    } catch (err: any) {
      let errorMessage = 'Signup failed. Please try again.';

      if (err.response?.data?.detail) {
        const detail = err.response.data.detail;
        if (Array.isArray(detail)) {
          errorMessage = detail.map((e: any) => e.msg || e.message || String(e)).join(', ');
        } else if (typeof detail === 'object') {
          errorMessage = JSON.stringify(detail);
        } else {
          errorMessage = String(detail);
        }
      } else if (err.message) {
        errorMessage = err.message;
      }

      setError(errorMessage);
    }
  };

  const benefits = [
    { icon: TrendingUp, title: 'Technical Indicators', desc: 'RSI, MACD, Bollinger Bands & more' },
    { icon: BarChart3, title: 'Multiple AI Models', desc: 'LSTM, Prophet, and statistical analysis' },
    { icon: Shield, title: 'Sentiment Analysis', desc: 'News & social media sentiment tracking' },
    { icon: Zap, title: 'Trend Detection', desc: 'Automatic pattern recognition' }
  ];

  const pricingFeatures = [
    'Unlimited stock analyses',
    'Real-time market data',
    'AI prediction models',
    'Portfolio tracking',
    'Price alerts',
    'Priority support'
  ];

  return (
    <div className="min-h-screen bg-gradient-to-br from-slate-950 via-slate-900 to-emerald-950 flex items-center justify-center p-6 relative overflow-hidden">
      {/* Animated background */}
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

      <div className="w-full max-w-7xl grid lg:grid-cols-5 gap-8 relative z-10">
        {/* Left side - Branding & Benefits (3 columns) */}
        <motion.div
          initial={{ opacity: 0, x: -20 }}
          animate={{ opacity: 1, x: 0 }}
          transition={{ duration: 0.6 }}
          className="hidden lg:flex lg:col-span-3 flex-col justify-center space-y-8 pr-8"
        >
          <div>
            <Link href="/" className="inline-block">
              <NeuroVestLogo className="w-12 h-12 mb-6" />
            </Link>
            <motion.div
              initial={{ opacity: 0, y: 20 }}
              animate={{ opacity: 1, y: 0 }}
              transition={{ delay: 0.2 }}
              className="flex items-center mb-4"
            >
              <span className="px-4 py-1.5 rounded-full bg-gradient-to-r from-emerald-500/20 to-cyan-500/20 border border-emerald-500/30 text-emerald-400 text-sm font-semibold">
                Open Source Platform
              </span>
            </motion.div>

            <motion.h1
              className="text-5xl font-bold text-white mb-4"
              initial={{ opacity: 0, y: 20 }}
              animate={{ opacity: 1, y: 0 }}
              transition={{ delay: 0.3 }}
            >
              Start Your
              <span className="bg-gradient-to-r from-emerald-400 via-cyan-400 to-purple-400 bg-clip-text text-transparent"> AI Trading </span>
              Journey
            </motion.h1>
            <motion.p
              className="text-xl text-slate-400 mb-8"
              initial={{ opacity: 0, y: 20 }}
              animate={{ opacity: 1, y: 0 }}
              transition={{ delay: 0.4 }}
            >
              Harness the power of artificial intelligence for smarter market decisions
            </motion.p>
          </div>

          {/* Benefits Grid */}
          <div className="grid grid-cols-2 gap-4">
            {benefits.map((benefit, index) => (
              <motion.div
                key={index}
                initial={{ opacity: 0, y: 20 }}
                animate={{ opacity: 1, y: 0 }}
                transition={{ delay: 0.5 + index * 0.1 }}
                className="p-5 rounded-2xl bg-white/5 backdrop-blur-sm border border-white/10 hover:border-emerald-500/50 transition-all hover:bg-white/10 group"
              >
                <div className="flex items-start space-x-4">
                  <div className="p-3 rounded-xl bg-gradient-to-br from-emerald-500/20 to-cyan-500/20 group-hover:scale-110 transition-transform">
                    <benefit.icon className="w-6 h-6 text-emerald-400" />
                  </div>
                  <div className="flex-1">
                    <h3 className="text-white font-semibold mb-1">{benefit.title}</h3>
                    <p className="text-sm text-slate-400">{benefit.desc}</p>
                  </div>
                </div>
              </motion.div>
            ))}
          </div>

          {/* Pricing Card */}
          <motion.div
            initial={{ opacity: 0, y: 20 }}
            animate={{ opacity: 1, y: 0 }}
            transition={{ delay: 0.9 }}
            className="relative p-6 rounded-2xl bg-gradient-to-br from-emerald-500/10 to-cyan-500/10 border border-emerald-500/30 backdrop-blur-sm overflow-hidden"
          >
            <div className="absolute top-0 right-0 px-4 py-1.5 bg-gradient-to-r from-emerald-500 to-cyan-500 rounded-bl-2xl">
              <span className="text-xs font-bold text-white flex items-center">
                <Crown className="w-3 h-3 mr-1" />
                FREE FOREVER
              </span>
            </div>

            <h3 className="text-2xl font-bold text-white mb-2 mt-4">Everything Included</h3>
            <p className="text-slate-400 mb-4 text-sm">No credit card required. Start analyzing immediately.</p>

            <div className="grid grid-cols-2 gap-2">
              {pricingFeatures.map((feature, index) => (
                <div key={index} className="flex items-center text-sm">
                  <CheckCircle2 className="w-4 h-4 text-emerald-400 mr-2 flex-shrink-0" />
                  <span className="text-slate-300">{feature}</span>
                </div>
              ))}
            </div>
          </motion.div>
        </motion.div>

        {/* Right side - Signup Form (2 columns) */}
        <motion.div
          initial={{ opacity: 0, x: 20 }}
          animate={{ opacity: 1, x: 0 }}
          transition={{ duration: 0.6 }}
          className="lg:col-span-2 flex items-center justify-center"
        >
          <div className="w-full max-w-md">
            <motion.div
              className="bg-slate-900/80 backdrop-blur-xl border border-emerald-500/20 rounded-3xl p-8 shadow-2xl shadow-emerald-500/10"
              whileHover={{ boxShadow: "0 25px 50px -12px rgba(16, 185, 129, 0.2)" }}
              transition={{ duration: 0.3 }}
            >
              {/* Mobile Logo */}
              <div className="lg:hidden mb-6 text-center">
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
                  <Users className="w-4 h-4 text-emerald-400 mr-2" />
                  <span className="text-sm font-semibold text-emerald-400">Join NeuroVest</span>
                </motion.div>

                <h2 className="text-3xl font-bold text-white mb-2">Create your account</h2>
                <p className="text-slate-400">Start trading smarter in seconds</p>
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
              <form onSubmit={handleSubmit} className="space-y-4">
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
                    placeholder="Min. 8 characters"
                    required
                    disabled={isLoading}
                    className="w-full px-4 py-3 bg-slate-800/50 border border-slate-700 rounded-xl text-white placeholder-slate-500 focus:border-emerald-500 focus:ring-2 focus:ring-emerald-500/20 transition-all outline-none disabled:opacity-50"
                  />
                </div>

                <div>
                  <label className="block text-emerald-400 text-sm font-semibold mb-2">
                    Confirm Password
                  </label>
                  <motion.input
                    whileFocus={{ scale: 1.01 }}
                    type="password"
                    value={formData.confirmPassword}
                    onChange={(e) => setFormData({ ...formData, confirmPassword: e.target.value })}
                    placeholder="Re-enter password"
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
                  className="w-full py-3.5 bg-gradient-to-r from-emerald-500 to-cyan-500 hover:from-emerald-600 hover:to-cyan-600 text-white font-bold rounded-xl shadow-lg shadow-emerald-500/30 disabled:opacity-50 disabled:cursor-not-allowed transition-all flex items-center justify-center group mt-6"
                >
                  {isLoading ? (
                    <span>Creating Account...</span>
                  ) : (
                    <>
                      <span>Create Free Account</span>
                      <ArrowRight className="w-5 h-5 ml-2 group-hover:translate-x-1 transition-transform" />
                    </>
                  )}
                </motion.button>
              </form>

              {/* Trust Indicators */}
              <div className="mt-6 p-4 rounded-xl bg-emerald-500/5 border border-emerald-500/20">
                <div className="grid grid-cols-3 gap-3 text-center">
                  <div>
                    <div className="text-xs text-slate-400 mb-1">Instant</div>
                    <div className="text-sm font-semibold text-emerald-400">Setup</div>
                  </div>
                  <div>
                    <div className="text-xs text-slate-400 mb-1">100%</div>
                    <div className="text-sm font-semibold text-emerald-400">Free</div>
                  </div>
                  <div>
                    <div className="text-xs text-slate-400 mb-1">No Credit</div>
                    <div className="text-sm font-semibold text-emerald-400">Card</div>
                  </div>
                </div>
              </div>

              {/* Footer Links */}
              <div className="mt-6 text-center space-y-3">
                <p className="text-slate-400 text-sm">
                  Already have an account?{' '}
                  <Link href="/auth/login" className="text-emerald-400 hover:text-emerald-300 font-semibold transition-colors">
                    Sign in
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

            {/* Security Badges */}
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
                Educational Use
              </div>
              <div className="flex items-center">
                <CheckCircle2 className="w-4 h-4 text-emerald-500 mr-1" />
                Open Source
              </div>
            </motion.div>
          </div>
        </motion.div>
      </div>
    </div>
  );
}