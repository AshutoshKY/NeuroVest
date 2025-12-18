'use client';

import { useEffect, useState } from 'react';
import Link from 'next/link';
import { motion } from 'framer-motion';
import { useAuthStore } from '@/store/authStore';
import deviceFingerprintService from '@/lib/fingerprint';
import { TrendingUp, Sparkles, ArrowRight, ChevronDown, Zap, Brain } from 'lucide-react';
import { NeuroVestLogo } from '@/components/NeuroVestLogo';

export default function Home() {
  const [mounted, setMounted] = useState(false);
  const { isAuthenticated, guestRequestsRemaining, checkGuestLimit } = useAuthStore();

  useEffect(() => {
    setMounted(true);
    deviceFingerprintService.getFingerprint();
    if (!isAuthenticated) {
      checkGuestLimit();
    }
  }, [isAuthenticated, checkGuestLimit]);

  const openAuthModal = (mode: 'login' | 'signup') => {
    window.location.href = mode === 'login' ? '/auth/login' : '/auth/signup';
  };

  return (
    <div className="min-h-screen bg-gradient-to-br from-slate-950 via-slate-900 to-slate-950">
      {/* Header */}
      <motion.header
        initial={{ y: -100 }}
        animate={{ y: 0 }}
        transition={{ duration: 0.6 }}
        className="fixed top-0 left-0 right-0 z-50 bg-slate-950/80 backdrop-blur-xl border-b border-slate-800"
      >
        <div className="max-w-7xl mx-auto px-4 sm:px-6 lg:px-8">
          <div className="flex items-center justify-between h-16">
            <motion.div
              className="flex items-center gap-2 cursor-pointer"
              whileHover={{ scale: 1.05 }}
            >
              <span className="text-2xl font-bold tracking-wider font-sans bg-clip-text text-transparent bg-gradient-to-r from-teal-400 to-purple-500">NEUR</span>
              <NeuroVestLogo className="h-8 w-8" />
              <span className="text-2xl font-bold tracking-wider font-sans bg-clip-text text-transparent bg-gradient-to-r from-purple-500 to-teal-400">VEST</span>
            </motion.div>

            {/* Desktop Auth Buttons */}
            <div className="flex items-center gap-4">
              {mounted && isAuthenticated ? (
                <motion.button
                  whileHover={{ scale: 1.05 }}
                  whileTap={{ scale: 0.95 }}
                  onClick={() => window.location.href = '/dashboard'}
                  className="px-6 py-2 bg-gradient-to-r from-emerald-500 to-cyan-500 text-white rounded-lg hover:shadow-lg hover:shadow-emerald-500/50 transition-shadow font-semibold"
                >
                  Dashboard
                </motion.button>
              ) : (
                <>
                  <motion.button
                    whileHover={{ scale: 1.05 }}
                    whileTap={{ scale: 0.95 }}
                    onClick={() => openAuthModal('login')}
                    className="px-4 py-2 text-slate-300 hover:text-white transition-colors font-medium"
                  >
                    Login
                  </motion.button>
                  <motion.button
                    whileHover={{ scale: 1.05 }}
                    whileTap={{ scale: 0.95 }}
                    onClick={() => openAuthModal('signup')}
                    className="px-6 py-2 bg-gradient-to-r from-emerald-500 to-cyan-500 text-white rounded-lg hover:shadow-lg hover:shadow-emerald-500/50 transition-shadow font-semibold"
                  >
                    Sign Up
                  </motion.button>
                </>
              )}
            </div>
          </div>
        </div>
      </motion.header>

      {/* Hero Section */}
      <section className="relative min-h-screen flex items-center justify-center overflow-hidden pt-16">
        {/* Animated Background */}
        <div className="absolute inset-0 z-0">
          <div className="absolute inset-0 bg-gradient-to-br from-emerald-500/10 via-transparent to-cyan-500/10" />
          <motion.div
            animate={{
              backgroundPosition: ['0% 0%', '100% 100%'],
            }}
            transition={{
              duration: 20,
              repeat: Infinity,
              repeatType: 'reverse',
            }}
            className="absolute inset-0 opacity-30"
            style={{
              backgroundImage: `url('https://images.unsplash.com/photo-1611974789855-9c2a0a7236a3?w=1920')`,
              backgroundSize: 'cover',
              backgroundPosition: 'center',
            }}
          />

          {/* Floating Orbs */}
          <motion.div
            animate={{
              y: [0, -30, 0],
              x: [0, 20, 0],
            }}
            transition={{
              duration: 8,
              repeat: Infinity,
              ease: 'easeInOut',
            }}
            className="absolute top-1/4 left-1/4 w-96 h-96 bg-emerald-500/20 rounded-full blur-3xl"
          />
          <motion.div
            animate={{
              y: [0, 30, 0],
              x: [0, -20, 0],
            }}
            transition={{
              duration: 10,
              repeat: Infinity,
              ease: 'easeInOut',
            }}
            className="absolute bottom-1/4 right-1/4 w-96 h-96 bg-cyan-500/20 rounded-full blur-3xl"
          />
        </div>

        {/* Content */}
        <div className="relative z-10 max-w-7xl mx-auto px-4 sm:px-6 lg:px-8 text-center">
          <motion.div
            initial={{ opacity: 0, y: 20 }}
            animate={{ opacity: 1, y: 0 }}
            transition={{ duration: 0.8 }}
            className="inline-flex items-center gap-2 px-4 py-2 bg-emerald-500/10 border border-emerald-500/20 rounded-full mb-8"
          >
            <Sparkles className="w-4 h-4 text-emerald-400" />
            <span className="text-emerald-400 font-semibold">
              {mounted && !isAuthenticated
                ? `${guestRequestsRemaining} Free Analyses Available`
                : 'AI-Powered Market Intelligence'}
            </span>
          </motion.div>

          <motion.h1
            initial={{ opacity: 0, y: 20 }}
            animate={{ opacity: 1, y: 0 }}
            transition={{ duration: 0.8, delay: 0.2 }}
            className="text-5xl sm:text-6xl lg:text-7xl font-bold text-white mb-6 bg-gradient-to-r from-white via-emerald-200 to-cyan-200 bg-clip-text text-transparent"
          >
            Neurovest
            <br />
            <span className="text-4xl sm:text-5xl lg:text-6xl">AI Stock Prediction Platform</span>
          </motion.h1>

          <motion.p
            initial={{ opacity: 0, y: 20 }}
            animate={{ opacity: 1, y: 0 }}
            transition={{ duration: 0.8, delay: 0.4 }}
            className="text-xl text-slate-300 mb-12 max-w-3xl mx-auto leading-relaxed"
          >
            Advanced AI-powered analysis combining 5 data sources, 7 technical indicators, and sentiment prediction for smarter trading decisions.
          </motion.p>

          <motion.div
            initial={{ opacity: 0, y: 20 }}
            animate={{ opacity: 1, y: 0 }}
            transition={{ duration: 0.8, delay: 0.6 }}
            className="flex flex-col sm:flex-row items-center justify-center gap-4"
          >
            <motion.button
              whileHover={{ scale: 1.05 }}
              whileTap={{ scale: 0.95 }}
              onClick={() => openAuthModal('signup')}
              className="px-8 py-4 bg-gradient-to-r from-emerald-500 to-cyan-500 text-white rounded-xl flex items-center gap-2 hover:shadow-2xl hover:shadow-emerald-500/50 transition-shadow group font-semibold"
            >
              Get Started Free
              <ArrowRight className="w-5 h-5 group-hover:translate-x-1 transition-transform" />
            </motion.button>

            <motion.button
              whileHover={{ scale: 1.05 }}
              whileTap={{ scale: 0.95 }}
              onClick={() => window.location.href = '/demo'}
              className="px-8 py-4 bg-slate-800/50 backdrop-blur-sm text-white rounded-xl border border-slate-700 hover:border-slate-600 transition-colors font-semibold"
            >
              Try Now
            </motion.button>
          </motion.div>

          <motion.p
            initial={{ opacity: 0 }}
            animate={{ opacity: 1 }}
            transition={{ duration: 0.8, delay: 0.8 }}
            className="text-slate-400 mt-6"
          >
            No credit card required • Free analysis included
          </motion.p>

          {/* Real Stats */}
          <motion.div
            initial={{ opacity: 0, y: 20 }}
            animate={{ opacity: 1, y: 0 }}
            transition={{ duration: 0.8, delay: 1 }}
            className="grid grid-cols-3 gap-8 mt-16 max-w-3xl mx-auto"
          >
            {[
              { value: '5+', label: 'Data Sources' },
              { value: '7', label: 'Tech Indicators' },
              { value: 'AI', label: 'Sentiment Engine' },
            ].map((stat, index) => (
              <motion.div
                key={index}
                whileHover={{ scale: 1.05 }}
                className="text-center"
              >
                <div className="text-3xl sm:text-4xl font-bold bg-gradient-to-r from-emerald-400 to-cyan-400 bg-clip-text text-transparent">
                  {stat.value}
                </div>
                <div className="text-slate-400 mt-2">{stat.label}</div>
              </motion.div>
            ))}
          </motion.div>
        </div>

        {/* Scroll Indicator */}
        <motion.div
          animate={{ y: [0, 10, 0] }}
          transition={{ duration: 2, repeat: Infinity }}
          className="absolute bottom-8 left-1/2 transform -translate-x-1/2"
        >
          <ChevronDown className="w-6 h-6 text-slate-500" />
        </motion.div>
      </section>

      {/* Features Section */}
      <section className="py-24 relative overflow-hidden">
        {/* Background Pattern */}
        <div className="absolute inset-0 opacity-10">
          <div className="absolute inset-0" style={{
            backgroundImage: `url('https://images.unsplash.com/photo-1611974789855-9c2a0a7236a3?w=1920')`,
            backgroundSize: 'cover',
            backgroundPosition: 'center',
          }} />
        </div>

        <div className="max-w-7xl mx-auto px-4 sm:px-6 lg:px-8 relative z-10">
          <motion.div
            initial={{ opacity: 0, y: 20 }}
            whileInView={{ opacity: 1, y: 0 }}
            viewport={{ once: true }}
            transition={{ duration: 0.6 }}
            className="text-center mb-16"
          >
            <h2 className="text-4xl sm:text-5xl font-bold text-white mb-4">
              Powerful Features for Smart Trading
            </h2>
            <p className="text-xl text-slate-400 max-w-2xl mx-auto">
              Everything you need to make informed trading decisions in one platform
            </p>
          </motion.div>

          <div className="grid md:grid-cols-3 gap-8">
            {[
              {
                icon: Zap,
                title: 'Multi-Source Data Integration',
                description: 'Real-time data from 5+ sources: Finnhub, Alpha Vantage, Yahoo Finance, Marketstack, and NSE/BSE Upstox APIs for comprehensive market coverage.',
                gradient: 'from-yellow-500 to-orange-500',
              },
              {
                icon: Brain,
                title: 'AI Sentiment & Predictions',
                description: 'AI-powered sentiment analysis using vector search across news, social media, and market data with predictive modeling for market movements.',
                gradient: 'from-purple-500 to-pink-500',
              },
              {
                icon: TrendingUp,
                title: '7 Professional Indicators',
                description: 'RSI (14-period), MACD with histogram, Bollinger Bands, SMA (10/50/200), trend analysis, and custom AI-powered signals for actionable insights.',
                gradient: 'from-emerald-500 to-cyan-500',
              },
            ].map((feature, index) => (
              <motion.div
                key={index}
                initial={{ opacity: 0, y: 30 }}
                whileInView={{ opacity: 1, y: 0 }}
                viewport={{ once: true }}
                transition={{ duration: 0.6, delay: index * 0.2 }}
                whileHover={{ y: -10 }}
                className="relative group"
              >
                <div className="relative bg-slate-900/90 backdrop-blur-xl border border-slate-800 rounded-2xl p-8 group-hover:border-slate-700 transition-colors">
                  {/* Icon */}
                  <motion.div
                    whileHover={{ rotate: 360 }}
                    transition={{ duration: 0.6 }}
                    className={`w-14 h-14 bg-gradient-to-br ${feature.gradient} rounded-xl flex items-center justify-center mb-6`}
                  >
                    <feature.icon className="w-7 h-7 text-white" />
                  </motion.div>

                  {/* Content */}
                  <h3 className="text-2xl font-bold text-white mb-4">{feature.title}</h3>
                  <p className="text-slate-400 leading-relaxed">{feature.description}</p>

                  {/* Decorative Element */}
                  <motion.div
                    initial={{ width: 0 }}
                    whileInView={{ width: '100%' }}
                    viewport={{ once: true }}
                    transition={{ duration: 0.8, delay: index * 0.2 + 0.4 }}
                    className={`h-1 bg-gradient-to-r ${feature.gradient} mt-6 rounded-full`}
                  />
                </div>
              </motion.div>
            ))}
          </div>

          {/* Additional Feature Stats */}
          <motion.div
            initial={{ opacity: 0, y: 20 }}
            whileInView={{ opacity: 1, y: 0 }}
            viewport={{ once: true }}
            transition={{ duration: 0.6, delay: 0.8 }}
            className="mt-16 grid grid-cols-2 md:grid-cols-4 gap-6"
          >
            {[
              { value: '7', label: 'Indicators' },
              { value: '5+', label: 'Data Sources' },
              { value: 'Real-time', label: 'Market Data' },
              { value: 'AI', label: 'Predictions' },
            ].map((stat, index) => (
              <motion.div
                key={index}
                whileHover={{ scale: 1.05 }}
                className="bg-slate-900/50 backdrop-blur-xl border border-slate-800 rounded-xl p-6 text-center"
              >
                <div className="text-3xl font-bold bg-gradient-to-r from-emerald-400 to-cyan-400 bg-clip-text text-transparent">
                  {stat.value}
                </div>
                <div className="text-slate-400 mt-2">{stat.label}</div>
              </motion.div>
            ))}
          </motion.div>
        </div>
      </section>

      {/* Footer */}
      <footer className="border-t border-slate-800 py-12 bg-slate-950">
        <div className="max-w-7xl mx-auto px-4 sm:px-6 lg:px-8 text-center">
          <div className="mb-4 flex items-center justify-center gap-1">
            <span className="text-2xl font-bold tracking-wider font-sans bg-clip-text text-transparent bg-gradient-to-r from-teal-400 to-purple-500">NEUR</span>
            <NeuroVestLogo className="h-8 w-8" />
            <span className="text-2xl font-bold tracking-wider font-sans bg-clip-text text-transparent bg-gradient-to-r from-purple-500 to-teal-400">VEST</span>
          </div>
          <p className="text-slate-500 text-sm">
            © 2024 Neurovest AI. All rights reserved.
          </p>
        </div>
      </footer>
    </div>
  );
}