import { motion } from 'framer-motion';
import { Zap, Brain, TrendingUp } from 'lucide-react';

export function Features() {
  const features = [
    {
      icon: Zap,
      title: 'Real-Time Insights',
      description: 'Lightning-fast analysis with sub-100ms latency. Never miss a market movement.',
      gradient: 'from-yellow-500 to-orange-500',
    },
    {
      icon: Brain,
      title: 'AI Sentiment Analysis',
      description: 'Our models analyze thousands of news sources to predict market sentiment.',
      gradient: 'from-purple-500 to-pink-500',
    },
    {
      icon: TrendingUp,
      title: 'Technical Indicators',
      description: 'Automated RSI, MACD, Bollinger Bands, and 17 more professional indicators.',
      gradient: 'from-emerald-500 to-cyan-500',
    },
  ];

  return (
    <section id="features" className="py-24 relative overflow-hidden">
      {/* Background Pattern */}
      <div className="absolute inset-0 opacity-10">
        <div className="absolute inset-0" style={{
          backgroundImage: `url('https://images.unsplash.com/photo-1579226905180-636b76d96082?crop=entropy&cs=tinysrgb&fit=max&fm=jpg&ixid=M3w3Nzg4Nzd8MHwxfHNlYXJjaHwxfHxmaW5hbmNpYWwlMjBkYXRhJTIwY2hhcnRzfGVufDF8fHx8MTc2NTA4OTg2MHww&ixlib=rb-4.1.0&q=80&w=1080&utm_source=figma&utm_medium=referral')`,
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
          <h2 className="text-4xl sm:text-5xl text-white mb-4">
            Powerful Features for Smart Trading
          </h2>
          <p className="text-xl text-slate-400 max-w-2xl mx-auto">
            Everything you need to make informed trading decisions in one platform
          </p>
        </motion.div>

        <div className="grid md:grid-cols-3 gap-8">
          {features.map((feature, index) => (
            <motion.div
              key={index}
              initial={{ opacity: 0, y: 30 }}
              whileInView={{ opacity: 1, y: 0 }}
              viewport={{ once: true }}
              transition={{ duration: 0.6, delay: index * 0.2 }}
              whileHover={{ y: -10 }}
              className="relative group"
            >
              {/* Card Background with Gradient Border */}
              <div className="absolute inset-0 bg-gradient-to-r opacity-0 group-hover:opacity-100 transition-opacity duration-500 rounded-2xl blur-xl p-[2px]"
                style={{ background: `linear-gradient(to right, var(--tw-gradient-stops))` }}
              />
              
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
                <h3 className="text-2xl text-white mb-4">{feature.title}</h3>
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
            { value: '20+', label: 'Indicators' },
            { value: '100ms', label: 'Response Time' },
            { value: '24/7', label: 'Monitoring' },
            { value: '99%', label: 'Accuracy' },
          ].map((stat, index) => (
            <motion.div
              key={index}
              whileHover={{ scale: 1.05 }}
              className="bg-slate-900/50 backdrop-blur-xl border border-slate-800 rounded-xl p-6 text-center"
            >
              <div className="text-3xl bg-gradient-to-r from-emerald-400 to-cyan-400 bg-clip-text text-transparent">
                {stat.value}
              </div>
              <div className="text-slate-400 mt-2">{stat.label}</div>
            </motion.div>
          ))}
        </motion.div>
      </div>
    </section>
  );
}
