import { motion } from 'framer-motion';
import { BookOpen, Code, Video, MessageCircle, FileText, Terminal } from 'lucide-react';

export function Documentation() {
  const resources = [
    {
      icon: BookOpen,
      title: 'Getting Started Guide',
      description: 'Learn the basics and get up and running in minutes',
      color: 'from-blue-500 to-cyan-500',
    },
    {
      icon: Code,
      title: 'API Documentation',
      description: 'Integrate our powerful API into your applications',
      color: 'from-emerald-500 to-teal-500',
    },
    {
      icon: Video,
      title: 'Video Tutorials',
      description: 'Step-by-step video guides for all features',
      color: 'from-purple-500 to-pink-500',
    },
    {
      icon: Terminal,
      title: 'Technical Indicators',
      description: 'Comprehensive guide to all available indicators',
      color: 'from-orange-500 to-red-500',
    },
    {
      icon: FileText,
      title: 'Trading Strategies',
      description: 'Learn proven strategies from expert traders',
      color: 'from-yellow-500 to-orange-500',
    },
    {
      icon: MessageCircle,
      title: 'Community Forum',
      description: 'Connect with other traders and get support',
      color: 'from-indigo-500 to-purple-500',
    },
  ];

  return (
    <section id="docs" className="py-24 relative overflow-hidden">
      {/* Background */}
      <div className="absolute inset-0 opacity-5">
        <div className="absolute inset-0" style={{
          backgroundImage: `url('https://images.unsplash.com/photo-1658806277165-af0b60eb6733?crop=entropy&cs=tinysrgb&fit=max&fm=jpg&ixid=M3w3Nzg4Nzd8MHwxfHNlYXJjaHwxfHxtb2Rlcm4lMjB0ZWNobm9sb2d5JTIwYWJzdHJhY3R8ZW58MXx8fHwxNzY1MTEwODYyfDA&ixlib=rb-4.1.0&q=80&w=1080&utm_source=figma&utm_medium=referral')`,
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
            Documentation & Resources
          </h2>
          <p className="text-xl text-slate-400 max-w-2xl mx-auto">
            Everything you need to master the platform
          </p>
        </motion.div>

        <div className="grid md:grid-cols-2 lg:grid-cols-3 gap-6">
          {resources.map((resource, index) => (
            <motion.div
              key={index}
              initial={{ opacity: 0, scale: 0.9 }}
              whileInView={{ opacity: 1, scale: 1 }}
              viewport={{ once: true }}
              transition={{ duration: 0.5, delay: index * 0.1 }}
              whileHover={{ scale: 1.05 }}
              className="group cursor-pointer"
            >
              <div className="bg-slate-900/50 backdrop-blur-xl border border-slate-800 rounded-xl p-6 hover:border-slate-700 transition-all">
                {/* Icon */}
                <motion.div
                  whileHover={{ rotate: 360 }}
                  transition={{ duration: 0.6 }}
                  className={`w-12 h-12 bg-gradient-to-br ${resource.color} rounded-lg flex items-center justify-center mb-4`}
                >
                  <resource.icon className="w-6 h-6 text-white" />
                </motion.div>

                {/* Content */}
                <h3 className="text-xl text-white mb-2 group-hover:text-emerald-400 transition-colors">
                  {resource.title}
                </h3>
                <p className="text-slate-400">
                  {resource.description}
                </p>

                {/* Arrow */}
                <motion.div
                  initial={{ x: 0 }}
                  whileHover={{ x: 5 }}
                  className="mt-4 text-emerald-400 flex items-center gap-2"
                >
                  <span>Learn more</span>
                  <span>&rarr;</span>
                </motion.div>
              </div>
            </motion.div>
          ))}
        </div>

        {/* CTA Section */}
        <motion.div
          initial={{ opacity: 0, y: 20 }}
          whileInView={{ opacity: 1, y: 0 }}
          viewport={{ once: true }}
          transition={{ duration: 0.6, delay: 0.6 }}
          className="mt-16 bg-gradient-to-r from-emerald-500/10 to-cyan-500/10 border border-emerald-500/20 rounded-2xl p-8 text-center"
        >
          <h3 className="text-3xl text-white mb-4">
            Need Help Getting Started?
          </h3>
          <p className="text-slate-300 mb-6 max-w-2xl mx-auto">
            Our support team is available 24/7 to help you with any questions
          </p>
          <div className="flex flex-col sm:flex-row gap-4 justify-center">
            <motion.button
              whileHover={{ scale: 1.05 }}
              whileTap={{ scale: 0.95 }}
              className="px-6 py-3 bg-gradient-to-r from-emerald-500 to-cyan-500 text-white rounded-lg hover:shadow-xl hover:shadow-emerald-500/50 transition-shadow"
            >
              Contact Support
            </motion.button>
            <motion.button
              whileHover={{ scale: 1.05 }}
              whileTap={{ scale: 0.95 }}
              className="px-6 py-3 bg-slate-800 text-white rounded-lg border border-slate-700 hover:border-slate-600 transition-colors"
            >
              Schedule Demo
            </motion.button>
          </div>
        </motion.div>
      </div>
    </section>
  );
}
