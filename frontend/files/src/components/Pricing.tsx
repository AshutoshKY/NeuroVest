import { motion } from 'framer-motion';
import { Check, Star } from 'lucide-react';

interface PricingProps {
  onSelectPlan: () => void;
}

export function Pricing({ onSelectPlan }: PricingProps) {
  const plans = [
    {
      name: 'Free',
      price: '$0',
      period: 'forever',
      description: 'Perfect for getting started',
      features: [
        'Basic technical indicators',
        'Daily market insights',
        'Community support',
        'Mobile app access',
        'Up to 5 watchlists',
      ],
      gradient: 'from-slate-700 to-slate-800',
      popular: false,
    },
    {
      name: 'Pro',
      price: '$29',
      period: 'per month',
      description: 'For serious traders',
      features: [
        'All technical indicators',
        'Real-time AI sentiment analysis',
        'Priority support',
        'Advanced charting tools',
        'Unlimited watchlists',
        'Price alerts',
        'API access',
      ],
      gradient: 'from-emerald-500 to-cyan-500',
      popular: true,
    },
    {
      name: 'Enterprise',
      price: '$199',
      period: 'per month',
      description: 'For trading teams',
      features: [
        'Everything in Pro',
        'Custom AI models',
        'Dedicated account manager',
        'White-label solutions',
        'Team collaboration tools',
        'Advanced API access',
        'Custom integrations',
        '99.99% SLA',
      ],
      gradient: 'from-purple-500 to-pink-500',
      popular: false,
    },
  ];

  return (
    <section id="pricing" className="py-24 relative overflow-hidden">
      {/* Background Gradient */}
      <div className="absolute inset-0 bg-gradient-to-b from-transparent via-emerald-500/5 to-transparent" />

      <div className="max-w-7xl mx-auto px-4 sm:px-6 lg:px-8 relative z-10">
        <motion.div
          initial={{ opacity: 0, y: 20 }}
          whileInView={{ opacity: 1, y: 0 }}
          viewport={{ once: true }}
          transition={{ duration: 0.6 }}
          className="text-center mb-16"
        >
          <h2 className="text-4xl sm:text-5xl text-white mb-4">
            Simple, Transparent Pricing
          </h2>
          <p className="text-xl text-slate-400 max-w-2xl mx-auto">
            Choose the perfect plan for your trading needs
          </p>
        </motion.div>

        <div className="grid md:grid-cols-3 gap-8">
          {plans.map((plan, index) => (
            <motion.div
              key={index}
              initial={{ opacity: 0, y: 30 }}
              whileInView={{ opacity: 1, y: 0 }}
              viewport={{ once: true }}
              transition={{ duration: 0.6, delay: index * 0.1 }}
              whileHover={{ y: -10, scale: 1.02 }}
              className="relative"
            >
              {/* Popular Badge */}
              {plan.popular && (
                <motion.div
                  initial={{ opacity: 0, scale: 0 }}
                  whileInView={{ opacity: 1, scale: 1 }}
                  viewport={{ once: true }}
                  transition={{ duration: 0.4, delay: 0.8 }}
                  className="absolute -top-4 left-1/2 transform -translate-x-1/2 z-20"
                >
                  <div className="bg-gradient-to-r from-emerald-500 to-cyan-500 px-4 py-1 rounded-full flex items-center gap-1">
                    <Star className="w-4 h-4 text-white fill-white" />
                    <span className="text-white">Most Popular</span>
                  </div>
                </motion.div>
              )}

              {/* Card */}
              <div className={`relative bg-slate-900/90 backdrop-blur-xl border ${
                plan.popular ? 'border-emerald-500/50' : 'border-slate-800'
              } rounded-2xl p-8 h-full flex flex-col`}>
                {/* Plan Name */}
                <div className="mb-6">
                  <h3 className="text-2xl text-white mb-2">{plan.name}</h3>
                  <p className="text-slate-400">{plan.description}</p>
                </div>

                {/* Price */}
                <div className="mb-6">
                  <div className="flex items-baseline gap-2">
                    <span className={`text-5xl bg-gradient-to-r ${plan.gradient} bg-clip-text text-transparent`}>
                      {plan.price}
                    </span>
                  </div>
                  <span className="text-slate-400">/{plan.period}</span>
                </div>

                {/* Features */}
                <ul className="space-y-4 mb-8 flex-grow">
                  {plan.features.map((feature, featureIndex) => (
                    <motion.li
                      key={featureIndex}
                      initial={{ opacity: 0, x: -20 }}
                      whileInView={{ opacity: 1, x: 0 }}
                      viewport={{ once: true }}
                      transition={{ duration: 0.4, delay: index * 0.1 + featureIndex * 0.05 }}
                      className="flex items-start gap-3"
                    >
                      <Check className="w-5 h-5 text-emerald-400 flex-shrink-0 mt-0.5" />
                      <span className="text-slate-300">{feature}</span>
                    </motion.li>
                  ))}
                </ul>

                {/* CTA Button */}
                <motion.button
                  whileHover={{ scale: 1.05 }}
                  whileTap={{ scale: 0.95 }}
                  onClick={onSelectPlan}
                  className={`w-full py-3 rounded-xl transition-all ${
                    plan.popular
                      ? 'bg-gradient-to-r from-emerald-500 to-cyan-500 text-white hover:shadow-xl hover:shadow-emerald-500/50'
                      : 'bg-slate-800 text-white hover:bg-slate-700'
                  }`}
                >
                  {plan.name === 'Free' ? 'Get Started' : 'Start Free Trial'}
                </motion.button>
              </div>
            </motion.div>
          ))}
        </div>

        {/* Money Back Guarantee */}
        <motion.div
          initial={{ opacity: 0, y: 20 }}
          whileInView={{ opacity: 1, y: 0 }}
          viewport={{ once: true }}
          transition={{ duration: 0.6, delay: 0.4 }}
          className="mt-12 text-center text-slate-400"
        >
          <p>All paid plans include a 14-day money-back guarantee</p>
        </motion.div>
      </div>
    </section>
  );
}
