import { useState, useEffect } from 'react';
import { motion, AnimatePresence } from 'framer-motion';
import { Upload, MessageSquare, Sparkles, ArrowRight, Play, Pause } from 'lucide-react';

const ModernHowItWorks = () => {
  const [activeStep, setActiveStep] = useState(0);
  const [isAutoPlaying, setIsAutoPlaying] = useState(true);

  const steps = [
    {
      id: 1,
      title: "Importez vos documents",
      subtitle: "Glissez, déposez, c'est parti",
      description: "Uploadez vos PDF, documents Word ou tout autre format. Notre IA analyse instantanément le contenu pour le comprendre en profondeur.",
      icon: Upload,
      color: "from-blue-500 to-cyan-500",
      bgColor: "bg-blue-500/10",
      features: ["PDF, DOCX, TXT", "Analyse instantanée", "OCR intégré"]
    },
    {
      id: 2,
      title: "L'IA comprend tout",
      subtitle: "Intelligence artificielle avancée",
      description: "Notre technologie de pointe analyse, indexe et structure vos documents pour créer une base de connaissances intelligente.",
      icon: Sparkles,
      color: "from-purple-500 to-pink-500",
      bgColor: "bg-purple-500/10",
      features: ["NLP avancé", "Indexation smart", "Contextualisation"]
    },
    {
      id: 3,
      title: "Conversez naturellement",
      subtitle: "Dialogue fluide et intelligent",
      description: "Posez vos questions en langage naturel et obtenez des réponses précises basées sur vos documents, avec citations à l'appui.",
      icon: MessageSquare,
      color: "from-green-500 to-emerald-500",
      bgColor: "bg-green-500/10",
      features: ["Chat naturel", "Réponses précises", "Citations sources"]
    }
  ];

  useEffect(() => {
    if (!isAutoPlaying) return;
    
    const interval = setInterval(() => {
      setActiveStep((prev) => (prev + 1) % steps.length);
    }, 4000);

    return () => clearInterval(interval);
  }, [isAutoPlaying, steps.length]);

  return (
    <div className="relative min-h-screen overflow-hidden bg-gradient-to-br from-slate-900 via-blue-900 to-slate-900">
      {/* Background Effects */}
      <div className="absolute inset-0">
        <div className="absolute rounded-full top-1/4 left-1/4 w-96 h-96 bg-blue-500/20 blur-3xl animate-pulse"></div>
        <div className="absolute delay-1000 rounded-full bottom-1/4 right-1/4 w-96 h-96 bg-purple-500/20 blur-3xl animate-pulse"></div>
      </div>

      <div className="relative z-10 px-6 py-24 mx-auto max-w-7xl">
        {/* Header */}
        <motion.div
          initial={{ opacity: 0, y: 30 }}
          whileInView={{ opacity: 1, y: 0 }}
          transition={{ duration: 0.8 }}
          viewport={{ once: true }}
          className="mb-20 text-center"
        >
          <motion.div
            initial={{ scale: 0 }}
            whileInView={{ scale: 1 }}
            transition={{ duration: 0.6, delay: 0.2 }}
            className="inline-flex items-center px-4 py-2 mb-6 text-sm font-medium text-blue-300 border rounded-full bg-blue-500/10 border-blue-500/20"
          >
            <Sparkles className="w-4 h-4 mr-2" />
            Comment ça fonctionne
          </motion.div>
          
          <h2 className="mb-6 text-6xl font-bold text-transparent bg-gradient-to-r from-white to-blue-200 bg-clip-text">
            Trois étapes pour révolutionner
            <br />
            <span className="text-5xl text-blue-400">vos documents</span>
          </h2>
          
          <p className="max-w-2xl mx-auto text-xl leading-relaxed text-slate-300">
            Transformez n'importe quel document en assistant IA conversationnel en quelques secondes
          </p>
        </motion.div>

        {/* Main Content */}
        <div className="grid items-center gap-16 lg:grid-cols-2">
          {/* Left Side - Steps Navigation */}
          <div className="space-y-6">
            <div className="flex items-center justify-between mb-8">
              <h3 className="text-2xl font-bold text-white">Le processus</h3>
              <button
                onClick={() => setIsAutoPlaying(!isAutoPlaying)}
                className="flex items-center px-4 py-2 text-sm text-blue-300 transition-colors border rounded-full bg-blue-500/10 border-blue-500/20 hover:bg-blue-500/20"
              >
                {isAutoPlaying ? <Pause className="w-4 h-4 mr-2" /> : <Play className="w-4 h-4 mr-2" />}
                {isAutoPlaying ? 'Pause' : 'Play'}
              </button>
            </div>

            {steps.map((step, index) => (
              <motion.div
                key={step.id}
                onClick={() => {
                  setActiveStep(index);
                  setIsAutoPlaying(false);
                }}
                className={`relative cursor-pointer p-6 rounded-2xl border-2 transition-all duration-500 ${
                  activeStep === index
                    ? 'bg-white/10 border-white/30 shadow-2xl backdrop-blur-lg'
                    : 'bg-white/5 border-white/10 hover:bg-white/8 hover:border-white/20'
                }`}
                whileHover={{ scale: 1.02 }}
                whileTap={{ scale: 0.98 }}
              >
                <div className="flex items-start space-x-4">
                  <div className={`w-12 h-12 rounded-xl bg-gradient-to-r ${step.color} flex items-center justify-center flex-shrink-0`}>
                    <step.icon className="w-6 h-6 text-white" />
                  </div>
                  
                  <div className="flex-1 min-w-0">
                    <div className="flex items-center mb-2 space-x-3">
                      <span className="text-2xl font-bold text-white">{step.id}</span>
                      <h4 className="text-lg font-bold text-white">{step.title}</h4>
                    </div>
                    <p className="mb-3 text-sm text-blue-200">{step.subtitle}</p>
                    
                    <AnimatePresence>
                      {activeStep === index && (
                        <motion.div
                          initial={{ opacity: 0, height: 0 }}
                          animate={{ opacity: 1, height: 'auto' }}
                          exit={{ opacity: 0, height: 0 }}
                          transition={{ duration: 0.3 }}
                        >
                          <p className="mb-4 text-sm leading-relaxed text-slate-300">
                            {step.description}
                          </p>
                          <div className="flex flex-wrap gap-2">
                            {step.features.map((feature, idx) => (
                              <span
                                key={idx}
                                className="px-3 py-1 text-xs font-medium text-blue-300 border rounded-full bg-blue-500/20 border-blue-500/30"
                              >
                                {feature}
                              </span>
                            ))}
                          </div>
                        </motion.div>
                      )}
                    </AnimatePresence>
                  </div>

                  {activeStep === index && (
                    <motion.div
                      initial={{ scale: 0 }}
                      animate={{ scale: 1 }}
                      className="flex-shrink-0 w-3 h-3 mt-2 bg-green-400 rounded-full"
                    />
                  )}
                </div>

                {/* Progress bar */}
                {activeStep === index && (
                  <motion.div
                    className="absolute bottom-0 left-0 h-1 rounded-full bg-gradient-to-r from-blue-500 to-purple-500"
                    initial={{ width: 0 }}
                    animate={{ width: '100%' }}
                    transition={{ duration: 4, ease: 'linear' }}
                  />
                )}
              </motion.div>
            ))}

            {/* Navigation Arrows */}
            <div className="flex justify-center pt-6 space-x-4">
              {steps.map((_, index) => (
                <button
                  key={index}
                  onClick={() => {
                    setActiveStep(index);
                    setIsAutoPlaying(false);
                  }}
                  className={`w-3 h-3 rounded-full transition-all duration-300 ${
                    activeStep === index
                      ? 'bg-blue-400 w-8'
                      : 'bg-white/20 hover:bg-white/40'
                  }`}
                />
              ))}
            </div>
          </div>

          {/* Right Side - Visual Demo */}
          <div className="relative">
            <AnimatePresence mode="wait">
              <motion.div
                key={activeStep}
                initial={{ opacity: 0, x: 50, rotateY: -15 }}
                animate={{ opacity: 1, x: 0, rotateY: 0 }}
                exit={{ opacity: 0, x: -50, rotateY: 15 }}
                transition={{ duration: 0.6, ease: 'easeInOut' }}
                className="relative"
              >
                {/* Main Visual Card */}
                <div className={`relative ${steps[activeStep].bgColor} backdrop-blur-lg rounded-3xl p-8 border border-white/10 shadow-2xl`}>
                  <div className="absolute inset-0 bg-gradient-to-br from-white/10 to-transparent rounded-3xl"></div>
                  
                  <div className="relative z-10">
                    {/* Icon */}
                    <div className={`w-20 h-20 mx-auto mb-6 rounded-2xl bg-gradient-to-r ${steps[activeStep].color} flex items-center justify-center`}>
                      <steps[activeStep].icon className="w-10 h-10 text-white" />
                    </div>

                    {/* Content */}
                    <div className="text-center">
                      <h4 className="mb-3 text-2xl font-bold text-white">
                        {steps[activeStep].title}
                      </h4>
                      <p className="text-lg leading-relaxed text-slate-300">
                        {steps[activeStep].description}
                      </p>
                    </div>

                    {/* Visual Elements */}
                    <div className="mt-8 space-y-3">
                      {steps[activeStep].features.map((feature, idx) => (
                        <motion.div
                          key={idx}
                          initial={{ opacity: 0, x: -20 }}
                          animate={{ opacity: 1, x: 0 }}
                          transition={{ delay: idx * 0.1 }}
                          className="flex items-center space-x-3 text-sm text-slate-300"
                        >
                          <div className="w-2 h-2 bg-green-400 rounded-full"></div>
                          <span>{feature}</span>
                        </motion.div>
                      ))}
                    </div>
                  </div>

                  {/* Floating Elements */}
                  <div className="absolute w-8 h-8 bg-blue-400 rounded-full -top-4 -right-4 animate-bounce opacity-60"></div>
                  <div className="absolute w-6 h-6 bg-purple-400 rounded-full -bottom-4 -left-4 animate-pulse opacity-60"></div>
                </div>

                {/* Connection Line to Next Step */}
                {activeStep < steps.length - 1 && (
                  <motion.div
                    initial={{ scaleX: 0 }}
                    animate={{ scaleX: 1 }}
                    transition={{ delay: 0.5, duration: 0.8 }}
                    className="absolute transform -translate-x-1/2 -bottom-8 left-1/2"
                  >
                    <ArrowRight className="w-6 h-6 text-blue-400 animate-pulse" />
                  </motion.div>
                )}
              </motion.div>
            </AnimatePresence>
          </div>
        </div>

        {/* Call to Action */}
        <motion.div
          initial={{ opacity: 0, y: 30 }}
          whileInView={{ opacity: 1, y: 0 }}
          transition={{ duration: 0.8 }}
          viewport={{ once: true }}
          className="mt-20 text-center"
        >
          <motion.button
            whileHover={{ scale: 1.05 }}
            whileTap={{ scale: 0.95 }}
            className="px-8 py-4 text-lg font-bold text-white transition-all duration-300 rounded-full shadow-lg bg-gradient-to-r from-blue-500 to-purple-600 hover:shadow-2xl"
          >
            Commencer maintenant
            <ArrowRight className="inline-block w-5 h-5 ml-2" />
          </motion.button>
        </motion.div>
      </div>
    </div>
  );
};

export default ModernHowItWorks;