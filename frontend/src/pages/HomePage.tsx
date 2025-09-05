import React, { useEffect, useState } from 'react';
import { Link } from 'react-router-dom';
import { motion } from 'framer-motion';
import logoBrand from '../assets/logoBrand.png'
import viDeo from '../assets/vedio.mp4'
import UploadImage from '../assets/uploadImage.jpg'
import RotatingText from '../components/common/RotatingText'
import DarkVeil from '../components/common/DarkVeil'
import converseImage from '../assets/converseImage.webp'
import LightRays from '../components/common/LightRays'
import analyseAIdoc from '../assets/analyseAIdoc.jpg'
import Collaboration from '../assets/Collaboration.webp'
import Security from '../assets/Security.webp'
import disponible24 from '../assets/disponible24.webp'
import interfaceint from '../assets/interface.webp'
import Insights from '../assets/Insights.webp'
import { 
  ChatBubbleLeftRightIcon, 
  DocumentArrowUpIcon, 
  ChartBarIcon,
  ArrowRightIcon,
  SparklesIcon,
  CheckIcon,
  PlayIcon,
  UserGroupIcon,
  ShieldCheckIcon,
  LightBulbIcon,
  RocketLaunchIcon,
  CpuChipIcon,
  CloudArrowUpIcon,
  MagnifyingGlassIcon
} from '@heroicons/react/24/outline';

interface Particle {
  id: number;
  x: number;
  y: number;
  size: number;
  duration: number;
  delay: number;
}

const HomePage: React.FC = () => {
  const [particles, setParticles] = useState<Particle[]>([]);
  const [currentStep, setCurrentStep] = useState(0);

  useEffect(() => {
    // Generate floating particles
    const newParticles = Array.from({ length: 40 }, (_, i) => ({
      id: i,
      x: Math.random() * 100,
      y: Math.random() * 100,
      size: Math.random() * 6 + 2,
      duration: Math.random() * 25 + 15,
      delay: Math.random() * 5
    }));
    setParticles(newParticles);

    // Auto-cycle through steps
    const interval = setInterval(() => {
      setCurrentStep((prev) => (prev + 1) % 3);
    }, 3000);

    return () => clearInterval(interval);
  }, []);

  const features = [
    {
      icon: ChatBubbleLeftRightIcon,
      title: 'Chat Intelligent Avancé',
      description: 'Conversez avec notre IA de dernière génération, capable de comprendre le contexte et de fournir des réponses précises et personnalisées.',
      color: 'from-blue-500 to-cyan-500',
      stats: '99.9% de précision'
    },
    {
      icon: DocumentArrowUpIcon,
      title: 'Analyse de Documents Intelligente',
      description: 'Téléchargez vos PDF, DOCX et TXT pour une analyse approfondie. Notre système RAG extrait et comprend le contenu pour des réponses contextuelles.',
      color: 'from-purple-500 to-pink-500',
      stats: '50+ formats supportés'
    },
    {
      icon: ChartBarIcon,
      title: 'Analytics & Insights',
      description: 'Obtenez des analyses détaillées de vos documents avec des graphiques interactifs, des métriques avancées et des rapports personnalisés.',
      color: 'from-green-500 to-emerald-500',
      stats: 'Temps réel'
    }
  ];

  const steps = [
    {
      number: '01',
      title: 'Téléchargez vos Documents',
      description: 'Glissez-déposez vos fichiers PDF, DOCX ou TXT dans notre interface sécurisée',
      icon: CloudArrowUpIcon,
      color: 'text-blue-500'
    },
    {
      number: '02',
      title: 'IA Analyse le Contenu',
      description: 'Notre système RAG traite et indexe intelligemment votre contenu',
      icon: CpuChipIcon,
      color: 'text-purple-500'
    },
    {
      number: '03',
      title: 'Obtenez des Réponses Précises',
      description: 'Posez vos questions et recevez des réponses basées sur vos documents',
      icon: MagnifyingGlassIcon,
      color: 'text-green-500'
    }
  ];

  const benefits = [
    'Interface intuitive et moderne',
    'Sécurité de niveau entreprise',
    'Support 24/7 en français',
    'API REST complète',
    'Intégration facile',
    'Analyses en temps réel'
  ];

  const testimonials = [
    {
      name: 'mustapha idabella',
      role: 'student engineer',
      company: 'TechCorp',
      content: 'FetChat a révolutionné notre façon de traiter les documents. L\'IA comprend parfaitement nos besoins.',
      avatar: 'https://images.pexels.com/photos/774909/pexels-photo-774909.jpeg?auto=compress&cs=tinysrgb&w=150&h=150&fit=crop'
    },
    {
      name: 'Jean Martin',
      role: 'Chef de Projet',
      company: 'InnovateLab',
      content: 'L\'analyse de documents n\'a jamais été aussi simple. Interface magnifique et résultats impressionnants.',
      avatar: 'https://images.pexels.com/photos/220453/pexels-photo-220453.jpeg?auto=compress&cs=tinysrgb&w=150&h=150&fit=crop'
    },
    {
      name: 'Sophie Laurent',
      role: 'Data Scientist',
      company: 'AI Solutions',
      content: 'La précision de l\'IA et la facilité d\'utilisation font de FetChat un outil indispensable.',
      avatar: 'https://images.pexels.com/photos/415829/pexels-photo-415829.jpeg?auto=compress&cs=tinysrgb&w=150&h=150&fit=crop'
    }
  ];

  return (
    <div className="relative overflow-hidden text-sm min--sh-screen bg-gradient-to-br from-gray-950 via-gray-900 to-gray-800">
      
      {/* Animated Particles */}
      {particles.map((particle) => (
        <motion.div
          key={particle.id}
          className="absolute rounded-full bg-white/10 backdrop-blur-sm"
          style={{
            left: `${particle.x}%`,
            top: `${particle.y}%`,
            width: `${particle.size}px`,
            height: `${particle.size}px`,
          }}
          animate={{
            y: [0, -40, 0],
            opacity: [0.2, 0.8, 0.2],
            scale: [1, 1.3, 1],
          }}
          transition={{
            duration: particle.duration,
            repeat: Infinity,
            ease: "easeInOut",
            delay: particle.delay,
          }}
        />
      ))}

      {/* Navigation Header */}


<div 
  className="relative min-h-screen bg-center bg-no-repeat bg-cover"
>
  {/* Background animé DarkVeil */}
  <div className="absolute inset-0 w-full h-full">
    <DarkVeil />
  </div>
  
  {/* Overlay léger par-dessus DarkVeil */}
  <div className="absolute inset-0 bg-gradient-to-br from-black/20 via-transparent to-purple-900/20"></div>
  
  {/* Navigation transparente */}
  <nav className="relative z-20 px-5 pt-3 bg-transparent backdrop-blur-sm">
    <div className="flex items-center justify-between w-full px-0">
      {/* Logo and Brand */}
      <motion.div
        initial={{ opacity: 0, x: -20 }}
        animate={{ opacity: 1, x: 0 }}
        transition={{ duration: 0.6 }}
        className="flex items-center ml-4 space-x-3"
      >
        <div className="flex items-center justify-center w-20 h-auto overflow-hidden rounded-xl">
          <img 
            src={logoBrand}
            alt="FetChat Bot Logo" 
            className=""
          />
        </div>
        <h1 className="text-4xl font-bold tracking-tight" style={{textShadow: '0 0 20px rgba(192, 132, 252, 0.5), 0 0 40px rgba(192, 132, 252, 0.3)'}}>
 <span className="font-[poppins] bg-gradient-to-r from-[#c084fc] to-white text-transparent bg-clip-text"> <span className='font-[poppins]'>F</span>ileChat</span>
</h1>
      </motion.div>

      {/* Navigation Buttons */}
      <motion.div
        initial={{ opacity: 0, x: 20 }}
        animate={{ opacity: 1, x: 0 }}
        transition={{ duration: 0.6, delay: 0.2 }}
        className="flex items-center mr-4 space-x-4"
      >
        <Link
          to="/login"
          className="px-6 py-2 text-white transition-all duration-200 hover:text-blue-200 hover:scale-105"
        >
          connecter
        </Link>
        <Link
          to="/signup"
          className="px-8 py-3 text-white transition-all duration-200 border bg-white/20 backdrop-blur-sm rounded-xl hover:bg-white/30 hover:scale-105 border-white/20"
        >
          s'inscrire
        </Link>
      </motion.div>
    </div>
  </nav>

  {/* Hero Section */}
  <div className="relative w-full px-0 pt-16 pb-10 z-2">
    <motion.div
      initial={{ opacity: 0, y: 30 }}
      animate={{ opacity: 1, y: 0 }}
      transition={{ duration: 0.8, delay: 0.3 }}
      className="text-center"
    >
      <motion.div
        initial={{ opacity: 0, scale: 0.8 }}
        animate={{ opacity: 1, scale: 1 }}
        transition={{ duration: 0.8, delay: 0.5 }}
        className="inline-flex items-center px-0 py-3 mb-8 space-x-2"
      >
        <RocketLaunchIcon className="w-5 h-5 text-blue-300" />
        <span className="font-medium text-blue-100">Nouvelle génération d'IA conversationnelle</span>
      </motion.div>
      
      <div className='text-lg'>
        <h1
          className="text-white font-[Poppins] leading-tight text-4xl sm:text-5xl md:text-6xl mb-10 font-bold text-center"
          style={{
            textShadow: '0 0 5px rgba(192, 132, 252, 0.4), 0 0 10px rgba(192, 132, 252, 0.3)',
          }}
        >
          L'IA qui 
          <span className="block text-transparent bg-gradient-to-r from-blue-400 via-purple-400 to-pink-400 bg-clip-text animate-pulse">
             comprend vos documents
          </span>
          <div className="relative flex justify-center mt-5">
            <RotatingText
              texts={[
 
                ' Obtenez des réponses',
                
              ]}
              mainClassName="px-0 sm:px-6 md:px-0 py-2 sm:py-2.5 md:py-3 justify-center rounded-xl relative z-10  font-bold bg-gradient-to-r from-blue-400 via-purple-400 to-pink-400 bg-clip-text animate-pulse text-gray-400"
              initial={{ y: '100%' }}
              animate={{ y: 0 }}
              exit={{ y: '-120%' }}
              staggerDuration={0.025}
              splitLevelClassName="overflow-hidden pb-1 sm:pb-1.5 md:pb-2"
              transition={{ type: 'spring', damping: 30, stiffness: 400 }}
              rotationInterval={2500}
            />
          </div>
        </h1>
        <br />
        <motion.p
          initial={{ opacity: 0 }}
          animate={{ opacity: 1 }}
          transition={{ duration: 0.8, delay: 0.8 }}
          className="max-w-5xl mx-auto mb-10 text-xl font-bold leading-relaxed text-blue-100"
        >
          Découvrez FileChat, la plateforme d'intelligence artificielle qui transforme 
          votre façon d'interagir avec vos documents. Uploadez, analysez et obtenez 
          des réponses intelligentes en temps réel.
        </motion.p>
      </div>
      
      <motion.div
        initial={{ opacity: 0, y: 20 }}
        animate={{ opacity: 1, y: 0 }}
        transition={{ duration: 0.8, delay: 1.1 }}
        className="flex flex-col items-center justify-center gap-6 mb-16 sm:flex-row"
      >
        <Link
          to="/signup"
          className="flex items-center px-10 py-5 space-x-3 text-xl font-bold text-white transition-all duration-300 border-2 group bg-gradient-to-r from-blue-800 to-purple-700 rounded-2xl hover:from-blue-600 hover:to-purple-700 hover:scale-105 hover:shadow-[0_0_20px_#3b82f6] border-white/20"
        >
          <span>Commencer Maintenant</span>
          <ArrowRightIcon className="w-6 h-6 transition-transform duration-300 group-hover:translate-x-2" />
        </Link>
        
        <button className="flex items-center px-10 py-5 space-x-3 text-xl font-bold text-white transition-all duration-300 border-2 group border-white/40 rounded-2xl hover:bg-white/10 backdrop-blur-sm hover:scale-105 hover:shadow-[0_0_20px_#3b82f6]">
          <PlayIcon className="w-6 h-6 transition-transform duration-300 group-hover:scale-110" />
          <span>Voir la Démo</span>
        </button>
      </motion.div>

      {/* Stats */}
      <motion.div
        initial={{ opacity: 0, y: 20 }}
        animate={{ opacity: 1, y: 0 }}
        transition={{ duration: 0.8, delay: 1.3 }}
        className="grid max-w-3xl grid-cols-1 gap-8 mx-auto md:grid-cols-3"
      >
        {[
          { number: '10K+', label: 'Utilisateurs Actifs' },
          { number: '1M+', label: 'Documents Traités' },
          { number: '99.9%', label: 'Temps de Disponibilité' }
        ].map((stat, index) => (
          <div key={index} className="p-4 text-center border backdrop-blur-sm bg-white/5 rounded-xl border-white/10">
            <div className="mb-2 text-4xl font-bold text-white">{stat.number}</div>
            <div className="text-blue-200">{stat.label}</div>
          </div>
        ))}
      </motion.div>
    </motion.div>
  </div>
</div>

      {/* How It Works Section - Design Professionnel avec couleurs blue, gray, white, purple sombre */}
<div className="relative z-10 w-auto px-[5px] pt-20 pb-20 mx-auto bg-gradient-to-t from-black via-gray-900 to-gray-950">
  {/* Header */}
  <motion.div
    initial={{ opacity: 0, y: 20 }}
    whileInView={{ opacity: 1, y: 0 }}
    transition={{ duration: 0.6 }}
    viewport={{ once: true }}
    className="mb-20 text-center"
  >
    <h2 className="mb-6 text-5xl font-bold text-white">
      Comment ça fonctionne ?
    </h2>
    <p className="max-w-2xl mx-auto text-xl text-gray-300">
      Trois étapes simples pour transformer vos documents en assistant intelligent
    </p>
  </motion.div>

  {/* Flow Container */}
  <div className="relative max-w-6xl mx-auto">
    
    {/* Step 1: Upload */}
    <motion.div
      initial={{ opacity: 0, y: 30 }}
      whileInView={{ opacity: 1, y: 0 }}
      transition={{ duration: 0.6, delay: 0.1 }}
      viewport={{ once: true }}
      className="flex flex-col items-center gap-12 mb-20 lg:flex-row"
    >
      {/* Step Content */}
      <div className="lg:w-1/2">
        <div className="flex items-center mb-6">
          <div className="flex items-center justify-center w-16 h-16 mr-6 text-2xl font-bold text-white shadow-lg bg-gradient-to-r from-blue-500 to-blue-600 rounded-2xl">
            1
          </div>
          <h3 className="text-3xl font-bold text-white">Uploadez vos Documents</h3>
        </div>
        <p className="mb-8 text-lg leading-relaxed text-gray-300">
          Glissez-déposez simplement vos fichiers dans notre interface intuitive. 
          Tous les formats populaires sont supportés.
        </p>
        
        {/* Features */}
        <div className="space-y-4">
          <div className="flex items-center p-3 rounded-lg bg-gray-800/30">
            <div className="flex items-center justify-center w-8 h-8 mr-4 rounded-full bg-blue-500/20">
              <div className="w-2 h-2 bg-blue-400 rounded-full"></div>
            </div>
            <span className="text-gray-300">PDF, DOCX, TXT, PPT et plus</span>
          </div>
          <div className="flex items-center p-3 rounded-lg bg-gray-800/30">
            <div className="flex items-center justify-center w-8 h-8 mr-4 rounded-full bg-blue-500/20">
              <div className="w-2 h-2 bg-blue-400 rounded-full"></div>
            </div>
            <span className="text-gray-300">Sécurité et confidentialité garanties</span>
          </div>
          <div className="flex items-center p-3 rounded-lg bg-gray-800/30">
            <div className="flex items-center justify-center w-8 h-8 mr-4 rounded-full bg-blue-500/20">
              <div className="w-2 h-2 bg-blue-400 rounded-full"></div>
            </div>
            <span className="text-gray-300">Upload instantané</span>
          </div>
        </div>
      </div>
      
      {/* Image Upload */}
      <div className="lg:w-1/2">
        <div className="relative overflow-hidden transition-all duration-300 border bg-gradient-to-br from-gray-800/50 to-gray-900/30 backdrop-blur-sm rounded-3xl border-gray-600/20 hover:border-blue-400/30">
          <img 
            src={UploadImage}
            alt="Upload de documents"
            className="object-cover w-full h-80 rounded-3xl"
          />
        </div>
      </div>
    </motion.div>

    {/* Arrow 1 */}
    <motion.div
      initial={{ opacity: 0, scale: 0.8 }}
      whileInView={{ opacity: 1, scale: 1 }}
      transition={{ duration: 0.5, delay: 0.3 }}
      viewport={{ once: true }}
      className="flex justify-center mb-20"
    >
      <div className="flex items-center">
        <div className="w-24 h-px bg-gradient-to-r from-blue-400 to-purple-500"></div>
        <div className="flex items-center justify-center w-12 h-12 mx-6 rounded-full shadow-lg bg-gradient-to-r from-blue-500 to-purple-600">
          <span className="text-xl text-white">→</span>
        </div>
        <div className="w-24 h-px bg-gradient-to-r from-purple-500 to-purple-600"></div>
      </div>
    </motion.div>

    {/* Step 2: Processing */}
    <motion.div
      initial={{ opacity: 0, y: 30 }}
      whileInView={{ opacity: 1, y: 0 }}
      transition={{ duration: 0.6, delay: 0.2 }}
      viewport={{ once: true }}
      className="flex flex-col items-center gap-12 mb-20 lg:flex-row-reverse"
    >
      {/* Step Content */}
      <div className="lg:w-1/2">
        <div className="flex items-center mb-6">
          <div className="flex items-center justify-center w-16 h-16 mr-6 text-2xl font-bold text-white shadow-lg bg-gradient-to-r from-purple-600 to-purple-700 rounded-2xl">
            2
          </div>
          <h3 className="text-3xl font-bold text-white">L'IA Analyse le Contenu</h3>
        </div>
        <p className="mb-8 text-lg leading-relaxed text-gray-300">
          Notre intelligence artificielle décompose et comprend chaque partie de votre document 
          pour créer une base de connaissances parfaite.
        </p>
        
        {/* Features */}
        <div className="space-y-4">
          <div className="flex items-center p-3 rounded-lg bg-gray-800/30">
            <div className="flex items-center justify-center w-8 h-8 mr-4 rounded-full bg-purple-500/20">
              <div className="w-2 h-2 bg-purple-400 rounded-full"></div>
            </div>
            <span className="text-gray-300">Analyse sémantique avancée</span>
          </div>
          <div className="flex items-center p-3 rounded-lg bg-gray-800/30">
            <div className="flex items-center justify-center w-8 h-8 mr-4 rounded-full bg-purple-500/20">
              <div className="w-2 h-2 bg-purple-400 rounded-full"></div>
            </div>
            <span className="text-gray-300">Extraction des concepts clés</span>
          </div>
          <div className="flex items-center p-3 rounded-lg bg-gray-800/30">
            <div className="flex items-center justify-center w-8 h-8 mr-4 rounded-full bg-purple-500/20">
              <div className="w-2 h-2 bg-purple-400 rounded-full"></div>
            </div>
            <span className="text-gray-300">Indexation intelligente</span>
          </div>
        </div>
      </div>
      
      {/* Image AI Processing */}
      <div className="lg:w-1/2">
        <div className="relative overflow-hidden transition-all duration-300 border bg-gradient-to-br from-gray-800/50 to-gray-900/30 backdrop-blur-sm rounded-3xl border-gray-600/20 hover:border-purple-400/30">
          <img 
            src={analyseAIdoc}
            alt="Traitement IA"
            className="object-cover w-full h-80 rounded-3xl"
          />
        </div>
      </div>
    </motion.div>

    {/* Arrow 2 */}
    <motion.div
      initial={{ opacity: 0, scale: 0.8 }}
      whileInView={{ opacity: 1, scale: 1 }}
      transition={{ duration: 0.5, delay: 0.5 }}
      viewport={{ once: true }}
      className="flex justify-center mb-20"
    >
      <div className="flex items-center">
        <div className="w-24 h-px bg-gradient-to-r from-purple-500 to-blue-500"></div>
        <div className="flex items-center justify-center w-12 h-12 mx-6 rounded-full shadow-lg bg-gradient-to-r from-purple-600 to-blue-500">
          <span className="text-xl text-white">→</span>
        </div>
        <div className="w-24 h-px bg-gradient-to-r from-blue-500 to-blue-600"></div>
      </div>
    </motion.div>

    {/* Step 3: Chat */}
    <motion.div
      initial={{ opacity: 0, y: 30 }}
      whileInView={{ opacity: 1, y: 0 }}
      transition={{ duration: 0.6, delay: 0.3 }}
      viewport={{ once: true }}
      className="flex flex-col items-center gap-12 mb-20 lg:flex-row"
    >
      {/* Step Content */}
      <div className="lg:w-1/2">
        <div className="flex items-center mb-6">
          <div className="flex items-center justify-center w-16 h-16 mr-6 text-2xl font-bold text-white shadow-lg bg-gradient-to-r from-blue-600 to-cyan-500 rounded-2xl">
            3
          </div>
          <h3 className="text-3xl font-bold text-white">Conversez Intelligemment</h3>
        </div>
        <p className="mb-8 text-lg leading-relaxed text-gray-300">
          Posez vos questions naturellement. Votre assistant IA comprend et répond 
          avec précision en se basant sur le contenu de vos documents.
        </p>
        
        {/* Features */}
        <div className="space-y-4">
          <div className="flex items-center p-3 rounded-lg bg-gray-800/30">
            <div className="flex items-center justify-center w-8 h-8 mr-4 rounded-full bg-cyan-500/20">
              <div className="w-2 h-2 rounded-full bg-cyan-400"></div>
            </div>
            <span className="text-gray-300">Questions en langage naturel</span>
          </div>
          <div className="flex items-center p-3 rounded-lg bg-gray-800/30">
            <div className="flex items-center justify-center w-8 h-8 mr-4 rounded-full bg-cyan-500/20">
              <div className="w-2 h-2 rounded-full bg-cyan-400"></div>
            </div>
            <span className="text-gray-300">Réponses avec sources citées</span>
          </div>
          <div className="flex items-center p-3 rounded-lg bg-gray-800/30">
            <div className="flex items-center justify-center w-8 h-8 mr-4 rounded-full bg-cyan-500/20">
              <div className="w-2 h-2 rounded-full bg-cyan-400"></div>
            </div>
            <span className="text-gray-300">Conversation illimitée</span>
          </div>
        </div>
      </div>
      
      {/* ai onversassionnel */}
      <div className="lg:w-1/2">
        <div className="relative overflow-hidden transition-all duration-300 border bg-gradient-to-br from-gray-800/50 to-gray-900/30 backdrop-blur-sm rounded-3xl border-gray-600/20 hover:border-blue-400/30">
          <img 
            src={converseImage}
            alt="Upload de documents"
            className="object-cover w-full h-80 rounded-3xl"
          />
        </div>
      </div>
    </motion.div>
  </div>
</div>
      {/* Benefits Section */}
    <div className="relative min-h-screen overflow-hidden bg-gradient-to-b from-gray-950 via-gray-800 to-slate-900">
  {/* Background Elements */}
  <div className="absolute inset-0 w-full h-full">
    <LightRays />
  </div>

  {/* Grid Pattern Overlay */}
  <div className="absolute inset-0 bg-[linear-gradient(rgba(255,255,255,.02)_1px,transparent_1px),linear-gradient(90deg,rgba(255,255,255,.02)_1px,transparent_1px)] bg-[size:50px_50px]"></div>

  <div className="container relative z-10 px-6 py-20 mx-auto max-w-7xl">
    {/* Header Section */}
    <div className="mb-20 text-center">
      <h2 className="mb-6 text-6xl font-bold leading-tight text-transparent md:text-7xl bg-gradient-to-r from-white via-blue-100 to-emerald-200 bg-clip-text">
        Pourquoi FileChat ?
      </h2>
      
      <p className="max-w-3xl mx-auto mb-12 text-xl leading-relaxed text-slate-300">
        Révolutionnez votre façon d'analyser et d'interagir avec vos documents grâce à l'intelligence artificielle de pointe
      </p>

      {/* Stats Grid */}
      <div className="grid max-w-4xl grid-cols-2 gap-8 mx-auto md:grid-cols-4">
        <div className="text-center cursor-pointer group">
          <div className="relative p-6 overflow-hidden transition-all duration-500 border bg-white/5 backdrop-blur-sm rounded-2xl border-white/10 hover:border-white/20 hover:bg-white/10 hover:scale-105">
            <div className="absolute inset-0 transition-transform duration-1000 -translate-x-full bg-gradient-to-r from-transparent via-white/5 to-transparent group-hover:translate-x-full"></div>
            <div className="mb-2 text-4xl font-bold text-emerald-400">99.9%</div>
            <div className="text-sm font-medium text-slate-400">Précision</div>
          </div>
        </div>
        <div className="text-center cursor-pointer group">
          <div className="relative p-6 overflow-hidden transition-all duration-500 border bg-white/5 backdrop-blur-sm rounded-2xl border-white/10 hover:border-white/20 hover:bg-white/10 hover:scale-105">
            <div className="absolute inset-0 transition-transform duration-1000 -translate-x-full bg-gradient-to-r from-transparent via-white/5 to-transparent group-hover:translate-x-full"></div>
            <div className="mb-2 text-4xl font-bold text-blue-400">10x</div>
            <div className="text-sm font-medium text-slate-400">Plus Rapide</div>
          </div>
        </div>
        <div className="text-center cursor-pointer group">
          <div className="relative p-6 overflow-hidden transition-all duration-500 border bg-white/5 backdrop-blur-sm rounded-2xl border-white/10 hover:border-white/20 hover:bg-white/10 hover:scale-105">
            <div className="absolute inset-0 transition-transform duration-1000 -translate-x-full bg-gradient-to-r from-transparent via-white/5 to-transparent group-hover:translate-x-full"></div>
            <div className="mb-2 text-4xl font-bold text-purple-400">24/7</div>
            <div className="text-sm font-medium text-slate-400">Disponible</div>
          </div>
        </div>
        <div className="text-center cursor-pointer group">
          <div className="relative p-6 overflow-hidden transition-all duration-500 border bg-white/5 backdrop-blur-sm rounded-2xl border-white/10 hover:border-white/20 hover:bg-white/10 hover:scale-105">
            <div className="absolute inset-0 transition-transform duration-1000 -translate-x-full bg-gradient-to-r from-transparent via-white/5 to-transparent group-hover:translate-x-full"></div>
            <div className="mb-2 text-4xl font-bold text-orange-400">10K+</div>
            <div className="text-sm font-medium text-slate-400">Utilisateurs</div>
          </div>
        </div>
      </div>
    </div>

    {/* Benefits Grid */}
    <div className="grid gap-8 mb-16 md:grid-cols-2 lg:grid-cols-3">
      {/* Benefit Card 1 */}
      <div className="relative p-8 overflow-hidden transition-all duration-500 border cursor-pointer group bg-white/5 backdrop-blur-sm rounded-3xl border-white/10 hover:border-white/20 hover:bg-white/10 hover:scale-105">
        {/* Image Container */}
        <div className="relative h-48 mb-6 overflow-hidden transition-transform duration-500 rounded-2xl bg-gradient-to-br from-slate-700 to-slate-800 group-hover:scale-105">
          <img src={analyseAIdoc} alt="Analyse Ultra-Rapide" className="object-cover w-full h-full" />
          <div className="absolute inset-0 bg-gradient-to-t from-black/20 to-transparent"></div>
          <div className="absolute inset-0 transition-transform duration-1000 -translate-x-full bg-gradient-to-r from-transparent via-white/10 to-transparent group-hover:translate-x-full"></div>
        </div>

        <div className="relative mb-4">
          <div className="inline-flex items-center justify-center transition-transform duration-300 shadow-lg w-14 h-14 bg-gradient-to-r from-emerald-500 to-blue-500 rounded-2xl group-hover:scale-110 group-hover:rotate-3">
            <svg className="w-6 h-6 text-white" fill="none" stroke="currentColor" viewBox="0 0 24 24">
              <path strokeLinecap="round" strokeLinejoin="round" strokeWidth={2} d="M13 10V3L4 14h7v7l9-11h-7z" />
            </svg>
          </div>
          <div className="absolute inset-0 transition-opacity duration-300 opacity-0 bg-gradient-to-r from-emerald-500 to-blue-500 rounded-2xl blur-lg group-hover:opacity-30"></div>
        </div>

        <h3 className="mb-3 text-xl font-bold text-white transition-colors duration-300 group-hover:text-emerald-100">
          Analyse Ultra-Rapide
        </h3>
        
        <p className="mb-4 leading-relaxed transition-colors duration-300 text-slate-400 group-hover:text-slate-300">
          Traitement instantané de vos documents avec IA avancée
        </p>

        <div className="flex items-center transition-all duration-300 transform translate-x-4 opacity-0 text-emerald-400 group-hover:opacity-100 group-hover:translate-x-0">
          <span className="mr-2 text-sm font-medium">En savoir plus</span>
          <svg className="w-4 h-4" fill="none" stroke="currentColor" viewBox="0 0 24 24">
            <path strokeLinecap="round" strokeLinejoin="round" strokeWidth={2} d="M9 5l7 7-7 7" />
          </svg>
        </div>

        <div className="absolute inset-0 transition-opacity duration-500 opacity-0 rounded-3xl bg-gradient-to-r from-emerald-500/10 to-blue-500/10 group-hover:opacity-100 -z-10"></div>
      </div>

      {/* Benefit Card 2 */}
      <div className="relative p-8 overflow-hidden transition-all duration-500 border cursor-pointer group bg-white/5 backdrop-blur-sm rounded-3xl border-white/10 hover:border-white/20 hover:bg-white/10 hover:scale-105">
        <div className="relative h-48 mb-6 overflow-hidden transition-transform duration-500 rounded-2xl bg-gradient-to-br from-slate-700 to-slate-800 group-hover:scale-105">
          <img src={Security} alt="Sécurité Maximale" className="object-cover w-full h-full" />
          <div className="absolute inset-0 bg-gradient-to-t from-black/20 to-transparent"></div>
          <div className="absolute inset-0 transition-transform duration-1000 -translate-x-full bg-gradient-to-r from-transparent via-white/10 to-transparent group-hover:translate-x-full"></div>
        </div>

        <div className="relative mb-4">
          <div className="inline-flex items-center justify-center transition-transform duration-300 shadow-lg w-14 h-14 bg-gradient-to-r from-emerald-500 to-blue-500 rounded-2xl group-hover:scale-110 group-hover:rotate-3">
            <svg className="w-6 h-6 text-white" fill="none" stroke="currentColor" viewBox="0 0 24 24">
              <path strokeLinecap="round" strokeLinejoin="round" strokeWidth={2} d="M9 12l2 2 4-4m5.618-4.016A11.955 11.955 0 0112 2.944a11.955 11.955 0 01-8.618 3.04A12.02 12.02 0 003 9c0 5.591 3.824 10.29 9 11.622 5.176-1.332 9-6.03 9-11.622 0-1.042-.133-2.052-.382-3.016z" />
            </svg>
          </div>
          <div className="absolute inset-0 transition-opacity duration-300 opacity-0 bg-gradient-to-r from-emerald-500 to-blue-500 rounded-2xl blur-lg group-hover:opacity-30"></div>
        </div>

        <h3 className="mb-3 text-xl font-bold text-white transition-colors duration-300 group-hover:text-emerald-100">
          Sécurité Maximale
        </h3>
        
        <p className="mb-4 leading-relaxed transition-colors duration-300 text-slate-400 group-hover:text-slate-300">
          Vos données protégées par cryptage de niveau bancaire
        </p>

        <div className="flex items-center transition-all duration-300 transform translate-x-4 opacity-0 text-emerald-400 group-hover:opacity-100 group-hover:translate-x-0">
          <span className="mr-2 text-sm font-medium">En savoir plus</span>
          <svg className="w-4 h-4" fill="none" stroke="currentColor" viewBox="0 0 24 24">
            <path strokeLinecap="round" strokeLinejoin="round" strokeWidth={2} d="M9 5l7 7-7 7" />
          </svg>
        </div>

        <div className="absolute inset-0 transition-opacity duration-500 opacity-0 rounded-3xl bg-gradient-to-r from-emerald-500/10 to-blue-500/10 group-hover:opacity-100 -z-10"></div>
      </div>

      {/* Benefit Card 3 */}
      <div className="relative p-8 overflow-hidden transition-all duration-500 border cursor-pointer group bg-white/5 backdrop-blur-sm rounded-3xl border-white/10 hover:border-white/20 hover:bg-white/10 hover:scale-105">
        <div className="relative h-48 mb-6 overflow-hidden transition-transform duration-500 rounded-2xl bg-gradient-to-br from-slate-700 to-slate-800 group-hover:scale-105">
          <img src={Insights} alt="Insights Précis" className="object-cover w-full h-full" />
          <div className="absolute inset-0 bg-gradient-to-t from-black/20 to-transparent"></div>
          <div className="absolute inset-0 transition-transform duration-1000 -translate-x-full bg-gradient-to-r from-transparent via-white/10 to-transparent group-hover:translate-x-full"></div>
        </div>

        <div className="relative mb-4">
          <div className="inline-flex items-center justify-center transition-transform duration-300 shadow-lg w-14 h-14 bg-gradient-to-r from-emerald-500 to-blue-500 rounded-2xl group-hover:scale-110 group-hover:rotate-3">
            <svg className="w-6 h-6 text-white" fill="none" stroke="currentColor" viewBox="0 0 24 24">
              <path strokeLinecap="round" strokeLinejoin="round" strokeWidth={2} d="M9 19v-6a2 2 0 00-2-2H5a2 2 0 00-2 2v6a2 2 0 002 2h2a2 2 0 002-2zm0 0V9a2 2 0 012-2h2a2 2 0 012 2v10m-6 0a2 2 0 002 2h2a2 2 0 002-2m0 0V5a2 2 0 012-2h2a2 2 0 012 2v14a2 2 0 01-2 2h-2a2 2 0 01-2-2z" />
            </svg>
          </div>
          <div className="absolute inset-0 transition-opacity duration-300 opacity-0 bg-gradient-to-r from-emerald-500 to-blue-500 rounded-2xl blur-lg group-hover:opacity-30"></div>
        </div>

        <h3 className="mb-3 text-xl font-bold text-white transition-colors duration-300 group-hover:text-emerald-100">
          Insights Précis
        </h3>
        
        <p className="mb-4 leading-relaxed transition-colors duration-300 text-slate-400 group-hover:text-slate-300">
          Extraction d'informations clés avec 99.9% de précision
        </p>

        <div className="flex items-center transition-all duration-300 transform translate-x-4 opacity-0 text-emerald-400 group-hover:opacity-100 group-hover:translate-x-0">
          <span className="mr-2 text-sm font-medium">En savoir plus</span>
          <svg className="w-4 h-4" fill="none" stroke="currentColor" viewBox="0 0 24 24">
            <path strokeLinecap="round" strokeLinejoin="round" strokeWidth={2} d="M9 5l7 7-7 7" />
          </svg>
        </div>

        <div className="absolute inset-0 transition-opacity duration-500 opacity-0 rounded-3xl bg-gradient-to-r from-emerald-500/10 to-blue-500/10 group-hover:opacity-100 -z-10"></div>
      </div>

      {/* Benefit Card 4 */}
      <div className="relative p-8 overflow-hidden transition-all duration-500 border cursor-pointer group bg-white/5 backdrop-blur-sm rounded-3xl border-white/10 hover:border-white/20 hover:bg-white/10 hover:scale-105">
        <div className="relative h-48 mb-6 overflow-hidden transition-transform duration-500 rounded-2xl bg-gradient-to-br from-slate-700 to-slate-800 group-hover:scale-105">
          <img src={disponible24} alt="Disponibilité 24/7" className="object-cover w-full h-full" />
          <div className="absolute inset-0 bg-gradient-to-t from-black/20 to-transparent"></div>
          <div className="absolute inset-0 transition-transform duration-1000 -translate-x-full bg-gradient-to-r from-transparent via-white/10 to-transparent group-hover:translate-x-full"></div>
        </div>

        <div className="relative mb-4">
          <div className="inline-flex items-center justify-center transition-transform duration-300 shadow-lg w-14 h-14 bg-gradient-to-r from-emerald-500 to-blue-500 rounded-2xl group-hover:scale-110 group-hover:rotate-3">
            <svg className="w-6 h-6 text-white" fill="none" stroke="currentColor" viewBox="0 0 24 24">
              <path strokeLinecap="round" strokeLinejoin="round" strokeWidth={2} d="M12 8v4l3 3m6-3a9 9 0 11-18 0 9 9 0 0118 0z" />
            </svg>
          </div>
          <div className="absolute inset-0 transition-opacity duration-300 opacity-0 bg-gradient-to-r from-emerald-500 to-blue-500 rounded-2xl blur-lg group-hover:opacity-30"></div>
        </div>

        <h3 className="mb-3 text-xl font-bold text-white transition-colors duration-300 group-hover:text-emerald-100">
          Disponibilité 24/7
        </h3>
        
        <p className="mb-4 leading-relaxed transition-colors duration-300 text-slate-400 group-hover:text-slate-300">
          Service continu pour vos besoins professionnels
        </p>

        <div className="flex items-center transition-all duration-300 transform translate-x-4 opacity-0 text-emerald-400 group-hover:opacity-100 group-hover:translate-x-0">
          <span className="mr-2 text-sm font-medium">En savoir plus</span>
          <svg className="w-4 h-4" fill="none" stroke="currentColor" viewBox="0 0 24 24">
            <path strokeLinecap="round" strokeLinejoin="round" strokeWidth={2} d="M9 5l7 7-7 7" />
          </svg>
        </div>

        <div className="absolute inset-0 transition-opacity duration-500 opacity-0 rounded-3xl bg-gradient-to-r from-emerald-500/10 to-blue-500/10 group-hover:opacity-100 -z-10"></div>
      </div>

      {/* Benefit Card 5 */}
      <div className="relative p-8 overflow-hidden transition-all duration-500 border cursor-pointer group bg-white/5 backdrop-blur-sm rounded-3xl border-white/10 hover:border-white/20 hover:bg-white/10 hover:scale-105">
        <div className="relative h-48 mb-6 overflow-hidden transition-transform duration-500 rounded-2xl bg-gradient-to-br from-slate-700 to-slate-800 group-hover:scale-105">
          <img src={Collaboration} alt="Collaboration Facile" className="object-cover w-full h-full" />
          <div className="absolute inset-0 bg-gradient-to-t from-black/20 to-transparent"></div>
          <div className="absolute inset-0 transition-transform duration-1000 -translate-x-full bg-gradient-to-r from-transparent via-white/10 to-transparent group-hover:translate-x-full"></div>
        </div>

        <div className="relative mb-4">
          <div className="inline-flex items-center justify-center transition-transform duration-300 shadow-lg w-14 h-14 bg-gradient-to-r from-emerald-500 to-blue-500 rounded-2xl group-hover:scale-110 group-hover:rotate-3">
            <svg className="w-6 h-6 text-white" fill="none" stroke="currentColor" viewBox="0 0 24 24">
              <path strokeLinecap="round" strokeLinejoin="round" strokeWidth={2} d="M12 4.354a4 4 0 110 5.292M15 21H3v-1a6 6 0 0112 0v1zm0 0h6v-1a6 6 0 00-9-5.197m13.5-9a2.5 2.5 0 11-5 0 2.5 2.5 0 015 0z" />
            </svg>
          </div>
          <div className="absolute inset-0 transition-opacity duration-300 opacity-0 bg-gradient-to-r from-emerald-500 to-blue-500 rounded-2xl blur-lg group-hover:opacity-30"></div>
        </div>

        <h3 className="mb-3 text-xl font-bold text-white transition-colors duration-300 group-hover:text-emerald-100">
          Collaboration Facile
        </h3>
        
        <p className="mb-4 leading-relaxed transition-colors duration-300 text-slate-400 group-hover:text-slate-300">
          Partagez et collaborez en temps réel avec votre équipe
        </p>

        <div className="flex items-center transition-all duration-300 transform translate-x-4 opacity-0 text-emerald-400 group-hover:opacity-100 group-hover:translate-x-0">
          <span className="mr-2 text-sm font-medium">En savoir plus</span>
          <svg className="w-4 h-4" fill="none" stroke="currentColor" viewBox="0 0 24 24">
            <path strokeLinecap="round" strokeLinejoin="round" strokeWidth={2} d="M9 5l7 7-7 7" />
          </svg>
        </div>

        <div className="absolute inset-0 transition-opacity duration-500 opacity-0 rounded-3xl bg-gradient-to-r from-emerald-500/10 to-blue-500/10 group-hover:opacity-100 -z-10"></div>
      </div>

      {/* Benefit Card 6 */}
      <div className="relative p-8 overflow-hidden transition-all duration-500 border cursor-pointer group bg-white/5 backdrop-blur-sm rounded-3xl border-white/10 hover:border-white/20 hover:bg-white/10 hover:scale-105">
        <div className="relative h-48 mb-6 overflow-hidden transition-transform duration-500 rounded-2xl bg-gradient-to-br from-slate-700 to-slate-800 group-hover:scale-105">
          <img src={interfaceint} alt="Interface Intuitive" className="object-cover w-full h-full" />
          <div className="absolute inset-0 bg-gradient-to-t from-black/20 to-transparent"></div>
          <div className="absolute inset-0 transition-transform duration-1000 -translate-x-full bg-gradient-to-r from-transparent via-white/10 to-transparent group-hover:translate-x-full"></div>
        </div>

        <div className="relative mb-4">
          <div className="inline-flex items-center justify-center transition-transform duration-300 shadow-lg w-14 h-14 bg-gradient-to-r from-emerald-500 to-blue-500 rounded-2xl group-hover:scale-110 group-hover:rotate-3">
            <svg className="w-6 h-6 text-white" fill="none" stroke="currentColor" viewBox="0 0 24 24">
              <path strokeLinecap="round" strokeLinejoin="round" strokeWidth={2} d="M5 3v4M3 5h4M6 17v4m-2-2h4m5-16l2.286 6.857L21 12l-5.714 2.143L13 21l-2.286-6.857L5 12l5.714-2.143L13 3z" />
            </svg>
          </div>
          <div className="absolute inset-0 transition-opacity duration-300 opacity-0 bg-gradient-to-r from-emerald-500 to-blue-500 rounded-2xl blur-lg group-hover:opacity-30"></div>
        </div>

        <h3 className="mb-3 text-xl font-bold text-white transition-colors duration-300 group-hover:text-emerald-100">
          Interface Intuitive
        </h3>
        
        <p className="mb-4 leading-relaxed transition-colors duration-300 text-slate-400 group-hover:text-slate-300">
          Design moderne et ergonomique pour une expérience optimale
        </p>

        <div className="flex items-center transition-all duration-300 transform translate-x-4 opacity-0 text-emerald-400 group-hover:opacity-100 group-hover:translate-x-0">
          <span className="mr-2 text-sm font-medium">En savoir plus</span>
          <svg className="w-4 h-4" fill="none" stroke="currentColor" viewBox="0 0 24 24">
            <path strokeLinecap="round" strokeLinejoin="round" strokeWidth={2} d="M9 5l7 7-7 7" />
          </svg>
        </div>

        <div className="absolute inset-0 transition-opacity duration-500 opacity-0 rounded-3xl bg-gradient-to-r from-emerald-500/10 to-blue-500/10 group-hover:opacity-100 -z-10"></div>
      </div>
    </div>

    {/* CTA Section */}
  </div>

  {/* Floating Elements */}
  <div className="absolute w-3 h-3 rounded-full top-20 left-20 bg-emerald-400 animate-bounce opacity-60" style={{ animationDelay: '0s' }}></div>
  <div className="absolute w-2 h-2 bg-blue-400 rounded-full top-40 right-32 animate-bounce opacity-40" style={{ animationDelay: '1s' }}></div>
  <div className="absolute w-4 h-4 bg-purple-400 rounded-full opacity-50 bottom-40 left-40 animate-bounce" style={{ animationDelay: '2s' }}></div>
  <div className="absolute w-2 h-2 bg-orange-400 rounded-full bottom-20 right-20 animate-bounce opacity-60" style={{ animationDelay: '3s' }}></div>
</div>

      {/* Section Témoignages Simple et Structurée */}

      <div className="relative z-10 px-6 pt-10 pb-24 mx-auto max-w-7xl">
        
        <motion.div
  initial={{ opacity: 0, y: 30 }}
  whileInView={{ opacity: 1, y: 0 }}
  transition={{ duration: 0.8 }}
  viewport={{ once: true }}
  className="relative p-16 overflow-hidden text-center bg-transparent border backdrop-blur-sm rounded-3xl border-white/20"
>
  {/* Vidéo de fond */}
  <video
    autoPlay
    muted
    loop
    playsInline
    className="absolute top-0 left-0 z-0 object-cover w-full h-full filter brightness-50"
  >
    <source src={viDeo} type="video/mp4" />
  </video>

  {/* Contenu visible */}
  <div className="relative z-10">
    <h2 className="mb-6 text-5xl font-bold text-white">
      Prêt à révolutionner votre workflow ?
    </h2>
    <p className="max-w-3xl mx-auto mb-12 text-xl text-white">
      Rejoignez des milliers d'utilisateurs qui ont déjà transformé leur façon de travailler avec FileChat
    </p>

    <div className="flex flex-col items-center justify-center gap-6 sm:flex-row">
      <Link
        to="/signup"
        className="flex items-center px-12 py-6 space-x-3 text-xl font-bold text-white transition-all duration-300 group bg-gradient-to-r from-blue-500 to-purple-600 rounded-2xl hover:from-blue-600 hover:to-purple-700 hover:scale-102 hover:shadow-glow-lg"
      >
        <span>Commencer Maintenant</span>
        <ArrowRightIcon className="w-6 h-6 transition-transform duration-300 group-hover:translate-x-2" />
      </Link>
    </div>
  </div>
</motion.div>

      </div>

      {/* Footer */}
      <footer className="relative z-10 py-12 border-t bg-black/30 backdrop-blur-sm border-white/10">
        <div className="px-6 mx-auto max-w-7xl">
          <div className="grid gap-8 mb-8 md:grid-cols-4">
            <div>
              <div className="flex items-center mb-4 space-x-3">
                <div className="flex items-center justify-center w-8 h-8 rounded-lg bg-gradient-to-r from-blue-400 to-purple-500">
                  <SparklesIcon className="w-5 h-5 text-white" />
                </div>
                <h3 className="text-xl font-bold text-white">FileChat</h3>
              </div>
              <p className="text-sm text-blue-200">
                L'avenir de l'intelligence artificielle conversationnelle
              </p>
            </div>
            
            <div>
              <h4 className="mb-4 font-semibold text-white">Produit</h4>
              <ul className="space-y-2 text-sm text-blue-200">
                <li><a href="#" className="transition-colors hover:text-white">Fonctionnalités</a></li>
                <li><a href="#" className="transition-colors hover:text-white">Tarifs</a></li>
                <li><a href="#" className="transition-colors hover:text-white">API</a></li>
              </ul>
            </div>
            
            <div>
              <h4 className="mb-4 font-semibold text-white">Support</h4>
              <ul className="space-y-2 text-sm text-blue-200">
                <li><a href="#" className="transition-colors hover:text-white">Documentation</a></li>
                <li><a href="#" className="transition-colors hover:text-white">Contact</a></li>
                <li><a href="#" className="transition-colors hover:text-white">FAQ</a></li>
              </ul>
            </div>
            
            <div>
              <h4 className="mb-4 font-semibold text-white">Entreprise</h4>
              <ul className="space-y-2 text-sm text-blue-200">
                <li><a href="#" className="transition-colors hover:text-white">À propos</a></li>
                <li><a href="#" className="transition-colors hover:text-white">Blog</a></li>
                <li><a href="#" className="transition-colors hover:text-white">Carrières</a></li>
              </ul>
            </div>
          </div>
          
          <div className="pt-8 text-center border-t border-white/10">
            <p className="text-sm text-blue-200">
              © 2025 FetChat. Tous droits réservés. Fait avec ❤️ en France.
            </p>
          </div>
        </div>
      </footer>
    </div>
  );
};

export default HomePage;