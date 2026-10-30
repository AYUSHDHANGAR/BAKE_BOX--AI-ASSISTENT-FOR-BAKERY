import React, { useState, useEffect, useRef } from 'react';
import { 
  Sparkles, ShoppingBag, User, Shield, LogIn, LogOut, CheckCircle2, 
  Clock, MapPin, Phone, ChefHat, MessageSquare, X, Send, Trash2, 
  Plus, Minus, AlertTriangle, Search, Filter, ArrowRight, Heart
} from 'lucide-react';

export default function App() {
  // Navigation & Tabs
  const [activeTab, setActiveTab] = useState('cakes'); // 'cakes', 'custom', 'snacks', 'patties', 'orders', 'admin'
  
  // Auth state
  const [user, setUser] = useState(null);
  const [token, setToken] = useState(localStorage.getItem('bakebox_token') || '');
  const [showAuthModal, setShowAuthModal] = useState(false);
  const [authMode, setAuthMode] = useState('login'); // 'login', 'register'
  const [authRole, setAuthRole] = useState('CUSTOMER'); // 'CUSTOMER', 'ADMIN'
  const [authEmail, setAuthEmail] = useState('');
  const [authPassword, setAuthPassword] = useState('');
  const [authFullName, setAuthFullName] = useState('');
  const [authPhone, setAuthPhone] = useState('');
  const [authError, setAuthError] = useState('');

  // Products state
  const [cakes, setCakes] = useState([]);
  const [customCakes, setCustomCakes] = useState([]);
  const [accessories, setAccessories] = useState([]);
  const [patties, setPatties] = useState([]);
  const [selectedFlavor, setSelectedFlavor] = useState('ALL');
  const [selectedCategory, setSelectedCategory] = useState('ALL');
  const [searchQuery, setSearchQuery] = useState('');
  const [loadingProducts, setLoadingProducts] = useState(false);
  const [currentPage, setCurrentPage] = useState(1);
  const [selectedCakeDetail, setSelectedCakeDetail] = useState(null);
  const itemsPerPage = 24;

  // Cart state
  const [cart, setCart] = useState([]);
  const [showCartDrawer, setShowCartDrawer] = useState(false);
  const [deliveryAddress, setDeliveryAddress] = useState('Mathura, Uttar Pradesh');
  const [orderSuccess, setOrderSuccess] = useState(null);

  // User Orders
  const [myOrders, setMyOrders] = useState([]);

  // Admin Dashboard
  const [adminMetrics, setAdminMetrics] = useState(null);
  const [adminOrders, setAdminOrders] = useState([]);

  // CHOCO AI Assistant Chat state
  const [showChocoModal, setShowChocoModal] = useState(false);
  const [chatMessages, setChatMessages] = useState([]);
  const [chatInput, setChatInput] = useState('');
  const [chatLoading, setChatLoading] = useState(false);
  const chatBottomRef = useRef(null);

  // Fetch current user on token change
  useEffect(() => {
    if (token) {
      fetch('/api/auth/me', {
        headers: { 'Authorization': `Bearer ${token}` }
      })
      .then(res => res.ok ? res.json() : null)
      .then(userData => {
        if (userData) {
          setUser(userData);
        } else {
          setToken('');
          localStorage.removeItem('bakebox_token');
        }
      })
      .catch(() => {
        setToken('');
        localStorage.removeItem('bakebox_token');
      });
    }
  }, [token]);

  // Load products
  useEffect(() => {
    setLoadingProducts(true);
    Promise.all([
      fetch('/api/products/cakes?limit=1000').then(r => r.json()),
      fetch('/api/products/custom-cakes?limit=200').then(r => r.json()),
      fetch('/api/products/accessories').then(r => r.json()),
      fetch('/api/products/bakery-raw').then(r => r.json())
    ]).then(([cakesData, customData, accData, rawData]) => {
      setCakes(cakesData.items || []);
      setCustomCakes(customData.items || []);
      setAccessories(accData.items || []);
      setPatties(rawData.items || []);
      setLoadingProducts(false);
    }).catch(err => {
      console.error("Products load error:", err);
      setLoadingProducts(false);
    });
  }, []);

  // Load user orders or admin data
  useEffect(() => {
    if (activeTab === 'orders' && token) {
      fetch('/api/orders/my-orders', {
        headers: { 'Authorization': `Bearer ${token}` }
      })
      .then(r => r.json())
      .then(data => setMyOrders(data.orders || []));
    }

    if (activeTab === 'admin' && token && user && (user.role === 'ADMIN' || user.role === 'STORE_OPERATOR')) {
      fetch('/api/admin/metrics', {
        headers: { 'Authorization': `Bearer ${token}` }
      })
      .then(r => r.json())
      .then(data => setAdminMetrics(data));

      fetch('/api/admin/orders', {
        headers: { 'Authorization': `Bearer ${token}` }
      })
      .then(r => r.json())
      .then(data => setAdminOrders(data.orders || []));
    }
  }, [activeTab, token, user]);

  // Load chat history when CHOCO modal opens
  useEffect(() => {
    if (showChocoModal && token && user) {
      fetch(`/api/choco/history?session_id=user_${user.id}_session`, {
        headers: { 'Authorization': `Bearer ${token}` }
      })
      .then(r => r.json())
      .then(data => {
        if (data.messages && data.messages.length > 0) {
          setChatMessages(data.messages);
        } else {
          // Initial welcome message
          setChatMessages([
            {
              role: 'assistant',
              content: `Radhe Radhe ${user.full_name.split(' ')[0]} ji! Shri Ram Baker's BAKEBOX mein aapka swagat hai! Main CHOCO hoon, aapka autonomous master baker assistant. Aaj aapke celebration ke liye kya khaas cake ya snacks dhoondein?`,
              ui_cards: []
            }
          ]);
        }
      });
    }
  }, [showChocoModal, token, user]);

  useEffect(() => {
    chatBottomRef.current?.scrollIntoView({ behavior: 'smooth' });
  }, [chatMessages, chatLoading]);

  // Auth Submit
  const handleAuthSubmit = async (e) => {
    e.preventDefault();
    setAuthError('');
    const endpoint = authMode === 'login' ? '/api/auth/login' : '/api/auth/register';
    const payload = authMode === 'login' 
      ? { email: authEmail, password: authPassword }
      : { email: authEmail, password: authPassword, full_name: authFullName, phone: authPhone, role: authRole };

    try {
      const res = await fetch(endpoint, {
        method: 'POST',
        headers: { 'Content-Type': 'application/json' },
        body: JSON.stringify(payload)
      });
      const data = await res.json();
      if (!res.ok) {
        throw new Error(data.detail || 'Authentication failed');
      }
      localStorage.setItem('bakebox_token', data.access_token);
      setToken(data.access_token);
      setUser(data.user);
      setShowAuthModal(false);
    } catch (err) {
      setAuthError(err.message);
    }
  };

  const handleLogout = () => {
    localStorage.removeItem('bakebox_token');
    setToken('');
    setUser(null);
    setMyOrders([]);
    setActiveTab('cakes');
  };

  // Quick Demo Logins
  const quickLogin = (email, pwd) => {
    setAuthEmail(email);
    setAuthPassword(pwd);
    setAuthMode('login');
  };

  // Cart operations
  const addToCart = (product, isCustom = false) => {
    const sku = product.SKU_ID || product.sku_id;
    const name = product.NAME || product.name || product.ITEM_NAME || product.item_name;
    const price = parseFloat(product.PRICE || product.price || product.PRICE_INR || product.price_inr || 249);
    const weight = product.WEIGHT_KG || product.weight_kg || 0.5;
    const img = product.IMAGE_PATH || product.image_url || product.image_path || '/catalog_images/CAKES_BRANDED/ACE/Black Forest/BAKEBOX_ACE_BlackForest_01.jpg';

    setCart(prev => {
      const existing = prev.find(item => item.sku_id === sku);
      if (existing) {
        return prev.map(item => item.sku_id === sku ? { ...item, quantity: item.quantity + 1 } : item);
      } else {
        return [...prev, {
          sku_id: sku,
          item_name: name,
          quantity: 1,
          unit_price: price,
          cake_base: 'Khoaa (Eggless)',
          cake_weight: `${weight}kg`,
          custom_message: '',
          image_url: img,
          is_custom: isCustom
        }];
      }
    });
    setShowCartDrawer(true);
  };

  const updateCartQty = (sku, delta) => {
    setCart(prev => prev.map(item => {
      if (item.sku_id === sku) {
        const newQty = item.quantity + delta;
        return newQty > 0 ? { ...item, quantity: newQty } : null;
      }
      return item;
    }).filter(Boolean));
  };

  const cartTotal = cart.reduce((sum, item) => sum + (item.unit_price * item.quantity), 0);

  // Place Order
  const handleCheckout = async () => {
    if (!user) {
      setShowAuthModal(true);
      return;
    }
    if (cart.length === 0) return;

    try {
      const res = await fetch('/api/orders/', {
        method: 'POST',
        headers: {
          'Content-Type': 'application/json',
          'Authorization': `Bearer ${token}`
        },
        body: JSON.stringify({
          customer_name: user.full_name,
          customer_phone: user.phone || '+91 9876543210',
          delivery_address: deliveryAddress,
          order_type: 'DELIVERY',
          special_notes: 'Bakebox Fresh Order from Customer Portal',
          items: cart.map(c => ({
            sku_id: c.sku_id,
            item_name: c.item_name,
            quantity: c.quantity,
            unit_price: c.unit_price,
            cake_base: c.cake_base,
            cake_weight: c.cake_weight,
            custom_message: c.custom_message
          }))
        })
      });
      const data = await res.json();
      if (!res.ok) throw new Error(data.detail || 'Order checkout failed');
      
      setOrderSuccess(data);
      setCart([]);
      setShowCartDrawer(false);
      setActiveTab('orders');
    } catch (err) {
      alert(`Order Error: ${err.message}`);
    }
  };

  // Send message to CHOCO
  const handleSendChoco = async (overrideMessage = null) => {
    const textToSend = overrideMessage || chatInput;
    if (!textToSend.trim() || !user || !token) return;

    const userMsg = { role: 'user', content: textToSend, ui_cards: [] };
    setChatMessages(prev => [...prev, userMsg]);
    if (!overrideMessage) setChatInput('');
    setChatLoading(true);

    try {
      const res = await fetch('/api/choco/chat', {
        method: 'POST',
        headers: {
          'Content-Type': 'application/json',
          'Authorization': `Bearer ${token}`
        },
        body: JSON.stringify({
          message: textToSend,
          session_id: `user_${user.id}_session`
        })
      });
      if (!res.ok) {
        const errText = await res.text();
        throw new Error(errText || 'Failed to chat with CHOCO');
      }
      const data = await res.json();

      setChatMessages(prev => [...prev, {
        role: 'assistant',
        content: data.reply,
        ui_cards: data.ui_cards || []
      }]);
    } catch (err) {
      setChatMessages(prev => [...prev, {
        role: 'assistant',
        content: `Khshama karein ji, technical error: ${err.message}. Kripya thoda ruk kar dubara puchein.`,
        ui_cards: []
      }]);
    } finally {
      setChatLoading(false);
    }
  };

  // Filtered standard cakes
  const filteredCakes = cakes.filter(c => {
    const matchesSearch = searchQuery === '' || 
      c.NAME.toLowerCase().includes(searchQuery.toLowerCase()) || 
      c.FLAVOR.toLowerCase().includes(searchQuery.toLowerCase()) ||
      (c.DESIGN_CODE && c.DESIGN_CODE.toLowerCase().includes(searchQuery.toLowerCase()));
    const matchesCategory = selectedCategory === 'ALL' || c.CATEGORY.toUpperCase() === selectedCategory;
    const matchesFlavor = selectedFlavor === 'ALL' || c.FLAVOR.toUpperCase() === selectedFlavor;
    return matchesSearch && matchesCategory && matchesFlavor;
  });

  const totalPages = Math.max(1, Math.ceil(filteredCakes.length / itemsPerPage));
  const displayedCakes = filteredCakes.slice((currentPage - 1) * itemsPerPage, currentPage * itemsPerPage);

  return (
    <div className="min-h-screen flex flex-col bg-[#FAF7F2] text-stone-900">
      
      {/* Top Banner: Mathura Branches & Store Guarantees */}
      <div className="bg-[#1C140E] text-amber-200 text-xs py-2 px-4 border-b border-amber-900/40">
        <div className="max-w-7xl mx-auto flex flex-col sm:flex-row items-center justify-between gap-2">
          <div className="flex items-center gap-4">
            <span className="flex items-center gap-1">
              <MapPin className="w-3.5 h-3.5 text-amber-400" />
              <span><strong>Branch 1:</strong> Bhagel Chaupal, Khatoti Kua (Mathura)</span>
            </span>
            <span className="hidden md:inline">|</span>
            <span className="hidden md:flex items-center gap-1">
              <MapPin className="w-3.5 h-3.5 text-amber-400" />
              <span><strong>Branch 2:</strong> Gausna (Mathura)</span>
            </span>
          </div>
          <div className="flex items-center gap-4 text-amber-300 font-medium">
            <span className="flex items-center gap-1">
              <Clock className="w-3.5 h-3.5 text-amber-400" />
              <span>Standard Baking Time: 3-4 Hours</span>
            </span>
            <span>|</span>
            <span className="flex items-center gap-1 text-emerald-400">
              <CheckCircle2 className="w-3.5 h-3.5" />
              <span>100% Pure Veg (Khoaa Eggless Available)</span>
            </span>
          </div>
        </div>
      </div>

      {/* Main Header */}
      <header className="sticky top-0 z-40 bg-white/95 backdrop-blur shadow-sm border-b border-stone-200">
        <div className="max-w-7xl mx-auto px-4 sm:px-6 lg:px-8 py-3.5 flex items-center justify-between gap-4">
          
          {/* Brand Logo */}
          <div className="flex items-center gap-3 cursor-pointer" onClick={() => setActiveTab('cakes')}>
            <div className="w-10 h-10 rounded-xl bg-gradient-to-tr from-amber-700 via-orange-600 to-amber-500 flex items-center justify-center shadow-md shadow-orange-900/20 text-white">
              <ChefHat className="w-6 h-6" />
            </div>
            <div>
              <div className="flex items-center gap-1.5">
                <span className="text-2xl font-extrabold tracking-tight text-stone-900">BAKEBOX</span>
                <span className="px-1.5 py-0.5 rounded text-[10px] font-bold bg-amber-100 text-amber-800 tracking-wider">AI 2.0</span>
              </div>
              <p className="text-[11px] font-semibold tracking-wide text-stone-500 uppercase">Shri Ram Baker • Mathura</p>
            </div>
          </div>

          {/* Search Bar */}
          <div className="hidden lg:flex items-center flex-1 max-w-md mx-6">
            <div className="relative w-full">
              <Search className="w-4 h-4 absolute left-3.5 top-3 text-stone-400" />
              <input 
                type="text" 
                placeholder="Search Black Forest, Red Velvet, Barbie Doll, Masala Patty..."
                value={searchQuery}
                onChange={e => setSearchQuery(e.target.value)}
                className="w-full pl-10 pr-4 py-2 bg-stone-100 border border-stone-200 rounded-full text-xs text-stone-800 focus:outline-none focus:ring-2 focus:ring-amber-500/30 focus:border-amber-600 transition"
              />
            </div>
          </div>

          {/* Action Buttons: Cart, Auth, CHOCO AI Trigger */}
          <div className="flex items-center gap-3">
            
            {/* CHOCO Assistant Quick Pill */}
            <button 
              onClick={() => setShowChocoModal(true)}
              className="relative px-3.5 py-2 rounded-full bg-gradient-to-r from-amber-600 to-orange-600 hover:from-amber-700 hover:to-orange-700 text-white text-xs font-bold shadow-md shadow-orange-600/20 flex items-center gap-2 transition transform active:scale-95"
            >
              <Sparkles className="w-4 h-4 text-amber-200 animate-pulse" />
              <span>Ask CHOCO AI</span>
              {!user && (
                <span className="w-2 h-2 rounded-full bg-red-400 ring-2 ring-white"></span>
              )}
            </button>

            {/* Cart Button */}
            <button 
              onClick={() => setShowCartDrawer(true)}
              className="relative p-2.5 rounded-full bg-stone-100 hover:bg-stone-200 text-stone-700 transition"
              title="Cart"
            >
              <ShoppingBag className="w-5 h-5" />
              {cart.length > 0 && (
                <span className="absolute -top-1 -right-1 w-5 h-5 rounded-full bg-orange-600 text-white text-[11px] font-extrabold flex items-center justify-center shadow">
                  {cart.reduce((s, i) => s + i.quantity, 0)}
                </span>
              )}
            </button>

            {/* User Profile / Login */}
            {user ? (
              <div className="flex items-center gap-2 pl-2 border-l border-stone-200">
                <div className="text-right hidden sm:block">
                  <p className="text-xs font-bold text-stone-900 leading-tight">{user.full_name}</p>
                  <span className={`inline-block text-[10px] font-bold px-1.5 py-0.2 rounded uppercase ${user.role === 'ADMIN' ? 'bg-red-100 text-red-800' : user.role === 'STORE_OPERATOR' ? 'bg-blue-100 text-blue-800' : 'bg-stone-200 text-stone-700'}`}>
                    {user.role}
                  </span>
                </div>
                <button 
                  onClick={handleLogout}
                  className="p-2 rounded-lg text-stone-500 hover:text-red-600 hover:bg-red-50 transition" 
                  title="Sign Out"
                >
                  <LogOut className="w-4 h-4" />
                </button>
              </div>
            ) : (
              <button 
                onClick={() => { setAuthMode('login'); setShowAuthModal(true); }}
                className="flex items-center gap-1.5 px-3.5 py-2 rounded-lg bg-stone-900 text-white hover:bg-stone-800 text-xs font-semibold shadow-sm transition"
              >
                <LogIn className="w-4 h-4" />
                <span>Sign In</span>
              </button>
            )}

          </div>

        </div>

        {/* Navigation Tabs Bar */}
        <div className="border-t border-stone-100 bg-stone-50/60">
          <div className="max-w-7xl mx-auto px-4 sm:px-6 lg:px-8 flex items-center gap-1 overflow-x-auto py-2">
            {[
              { id: 'cakes', label: '🎂 Standard Cakes', count: cakes.length },
              { id: 'custom', label: '👑 Custom Designer Cakes (1-on-1)', count: customCakes.length },
              { id: 'patties', label: '🥐 Fresh Oven Patties & Raw', count: patties.length },
              { id: 'snacks', label: '🎉 Party Accessories & Snacks', count: accessories.length },
              { id: 'orders', label: '📦 My Orders', count: myOrders.length },
              ...(user && (user.role === 'ADMIN' || user.role === 'STORE_OPERATOR') ? [
                { id: 'admin', label: '⚙️ Admin & Operator Dashboard', count: null }
              ] : [])
            ].map(tab => (
              <button
                key={tab.id}
                onClick={() => setActiveTab(tab.id)}
                className={`px-4 py-2 rounded-lg text-xs font-bold whitespace-nowrap transition flex items-center gap-1.5 ${
                  activeTab === tab.id 
                    ? 'bg-amber-600 text-white shadow-sm' 
                    : 'text-stone-600 hover:text-stone-900 hover:bg-stone-200/60'
                }`}
              >
                <span>{tab.label}</span>
                {tab.count !== null && (
                  <span className={`px-1.5 py-0.2 rounded-full text-[10px] ${activeTab === tab.id ? 'bg-amber-700 text-amber-100' : 'bg-stone-200 text-stone-600'}`}>
                    {tab.count}
                  </span>
                )}
              </button>
            ))}
          </div>
        </div>
      </header>

      {/* Main Content Area */}
      <main className="flex-1 max-w-7xl w-full mx-auto px-4 sm:px-6 lg:px-8 py-6">

        {/* Tab 1: Standard Cakes Catalog */}
        {activeTab === 'cakes' && (
          <div>
            {/* Category Banner & Filter Controls */}
            <div className="mb-6 flex flex-col sm:flex-row sm:items-center justify-between gap-4 bg-white p-4 rounded-2xl shadow-sm border border-stone-200">
              <div>
                <h1 className="text-xl font-extrabold text-stone-900 font-serif-title">Fresh Baked Standard Cakes</h1>
                <p className="text-xs text-stone-500 mt-0.5">Handcrafted on demand by Shri Ram Baker • Standard 3-4 hours baking wait time</p>
              </div>

              {/* Filters */}
              <div className="flex flex-wrap items-center gap-2">
                <div className="flex items-center gap-1 bg-stone-100 p-1 rounded-xl">
                  {['ALL', 'ACE', 'STAR', 'ELITE', 'PREMIUM'].map(cat => (
                    <button
                      key={cat}
                      onClick={() => { setSelectedCategory(cat); setCurrentPage(1); }}
                      className={`px-3 py-1 rounded-lg text-xs font-bold transition ${selectedCategory === cat ? 'bg-white text-orange-600 shadow-sm' : 'text-stone-600 hover:text-stone-900'}`}
                    >
                      {cat}
                    </button>
                  ))}
                </div>

                <select 
                  value={selectedFlavor} 
                  onChange={e => { setSelectedFlavor(e.target.value); setCurrentPage(1); }}
                  className="px-3 py-1.5 bg-stone-100 border border-stone-200 rounded-xl text-xs font-semibold text-stone-700 focus:outline-none focus:ring-2 focus:ring-amber-500"
                >
                  <option value="ALL">All Flavors (600+ Cakes)</option>
                  <option value="BLACK FOREST">Black Forest</option>
                  <option value="RED VELVET">Red Velvet</option>
                  <option value="CHOCOLATE">Chocolate</option>
                  <option value="PINEAPPLE">Pineapple</option>
                  <option value="BUTTERSCOTCH">Butterscotch</option>
                  <option value="STRAWBERRY">Strawberry</option>
                  <option value="VANILLA">Vanilla</option>
                  <option value="TRUFFLE">Truffle</option>
                  <option value="FRUIT">Fruit</option>
                </select>
              </div>
            </div>

            {/* Catalog Count Banner */}
            <div className="mb-4 flex items-center justify-between text-xs text-stone-500 px-1">
              <span>Showing <strong>{(currentPage - 1) * itemsPerPage + 1} - {Math.min(currentPage * itemsPerPage, filteredCakes.length)}</strong> of <strong>{filteredCakes.length}</strong> cakes (Total: {cakes.length} verified in IBM Db2)</span>
              <span>Page <strong>{currentPage}</strong> of <strong>{totalPages}</strong></span>
            </div>

            {/* Cakes Grid */}
            {loadingProducts ? (
              <div className="py-20 text-center text-stone-500">Loading BAKEBOX cake catalog from IBM Db2...</div>
            ) : filteredCakes.length === 0 ? (
              <div className="py-20 text-center text-stone-500">No cakes found matching your filter.</div>
            ) : (
              <>
                <div className="grid grid-cols-1 sm:grid-cols-2 md:grid-cols-3 lg:grid-cols-4 gap-6">
                  {displayedCakes.map(cake => (
                    <div key={cake.SKU_ID} onClick={() => setSelectedCakeDetail(cake)} className="bg-white rounded-2xl overflow-hidden border border-stone-200 shadow-sm hover:shadow-md transition flex flex-col group cursor-pointer">
                      
                      {/* Cake Image */}
                      <div className="relative aspect-square overflow-hidden bg-stone-100">
                        <img 
                          src={cake.IMAGE_PATH} 
                          alt={cake.NAME}
                          className="w-full h-full object-cover group-hover:scale-105 transition duration-500"
                          onError={(e) => {
                            e.target.src = 'https://images.unsplash.com/photo-1578985545062-69928b1d9587?w=500&auto=format&fit=crop&q=60';
                          }}
                        />
                        <span className={`absolute top-3 left-3 text-[10px] font-extrabold uppercase px-2 py-0.5 rounded-full shadow-sm ${cake.CATEGORY === 'PREMIUM' ? 'bg-amber-600 text-white' : 'bg-stone-900 text-white'}`}>
                          {cake.CATEGORY}
                        </span>
                        <span className="absolute bottom-3 right-3 text-[10px] font-bold px-2 py-0.5 rounded bg-white/90 backdrop-blur text-stone-800 shadow">
                          {cake.WEIGHT_KG} kg
                        </span>
                      </div>

                      {/* Cake Details */}
                      <div className="p-4 flex-1 flex flex-col justify-between">
                        <div>
                          <div className="flex items-center gap-1.5 text-[11px] font-bold text-amber-700 uppercase tracking-wide">
                            <span>{cake.FLAVOR}</span>
                            <span>•</span>
                            <span>{cake.SUB_CATEGORY}</span>
                          </div>
                          <h3 className="text-sm font-bold text-stone-900 line-clamp-1 mt-1">{cake.NAME}</h3>
                          <p className="text-xs text-stone-500 line-clamp-2 mt-1">{cake.VISUAL_FEATURES || cake.DESCRIPTION}</p>
                          
                          {/* Bases */}
                          <div className="mt-2.5 flex items-center gap-1 text-[10px] text-emerald-700 bg-emerald-50 px-2 py-1 rounded-md font-medium">
                            <CheckCircle2 className="w-3 h-3 text-emerald-600 flex-shrink-0" />
                            <span className="truncate">Khoaa, Veg Eggless & Egg Available</span>
                          </div>
                        </div>

                        {/* Price & Action */}
                        <div className="mt-4 pt-3 border-t border-stone-100 flex items-center justify-between gap-1.5">
                          <div>
                            <span className="text-[10px] text-stone-400 font-bold uppercase">Price</span>
                            <p className="text-base font-extrabold text-stone-900 leading-none">₹{parseFloat(cake.PRICE).toFixed(0)}</p>
                          </div>
                          <div className="flex items-center gap-1.5">
                            <button
                              onClick={(e) => {
                                e.stopPropagation();
                                setShowChocoModal(true);
                                handleSendChoco(`Bhaiya, mujhe is cake '${cake.NAME}' (SKU: ${cake.SKU_ID}, Flavor: ${cake.FLAVOR}, Weight: ${cake.WEIGHT_KG}kg) ke baare mein complete details aur recommendation bataiye.`);
                              }}
                              className="px-2 py-1.5 rounded-xl bg-amber-50 hover:bg-amber-100 text-amber-800 border border-amber-300 text-xs font-bold transition flex items-center gap-1 active:scale-95 shadow-sm"
                              title="Ask CHOCO about this cake"
                            >
                              <Sparkles className="w-3.5 h-3.5 text-amber-600" />
                              <span className="text-[11px]">Ask CHOCO</span>
                            </button>
                            <button
                              onClick={(e) => {
                                e.stopPropagation();
                                addToCart(cake);
                              }}
                              className="px-3 py-1.5 bg-stone-900 hover:bg-amber-600 text-white text-xs font-bold rounded-xl transition flex items-center gap-1 shadow-sm active:scale-95"
                            >
                              <ShoppingBag className="w-3.5 h-3.5" />
                              <span>Add</span>
                            </button>
                          </div>
                        </div>

                      </div>
                    </div>
                  ))}
                </div>

                {/* Pagination Bar */}
                {totalPages > 1 && (
                  <div className="mt-8 flex items-center justify-center gap-2">
                    <button
                      onClick={() => setCurrentPage(p => Math.max(1, p - 1))}
                      disabled={currentPage === 1}
                      className="px-3.5 py-1.5 rounded-xl border border-stone-300 text-xs font-bold text-stone-700 bg-white hover:bg-stone-50 disabled:opacity-40 transition"
                    >
                      Previous
                    </button>
                    {Array.from({ length: Math.min(7, totalPages) }, (_, i) => {
                      let pageNum = i + 1;
                      if (totalPages > 7 && currentPage > 4) {
                        pageNum = Math.min(totalPages - 6 + i, currentPage - 3 + i);
                      }
                      return (
                        <button
                          key={pageNum}
                          onClick={() => setCurrentPage(pageNum)}
                          className={`w-8 h-8 rounded-xl text-xs font-bold transition ${
                            currentPage === pageNum 
                              ? 'bg-amber-600 text-white shadow-sm' 
                              : 'bg-white border border-stone-200 text-stone-700 hover:bg-stone-100'
                          }`}
                        >
                          {pageNum}
                        </button>
                      );
                    })}
                    <button
                      onClick={() => setCurrentPage(p => Math.min(totalPages, p + 1))}
                      disabled={currentPage === totalPages}
                      className="px-3.5 py-1.5 rounded-xl border border-stone-300 text-xs font-bold text-stone-700 bg-white hover:bg-stone-50 disabled:opacity-40 transition"
                    >
                      Next
                    </button>
                  </div>
                )}
              </>
            )}
          </div>
        )}

        {/* Tab 2: Custom Designer Cakes (1-on-1 Consultation) */}
        {activeTab === 'custom' && (
          <div>
            <div className="mb-6 bg-gradient-to-r from-amber-900 via-stone-900 to-amber-950 text-white p-6 rounded-2xl shadow-md flex flex-col md:flex-row items-center justify-between gap-6">
              <div className="space-y-2">
                <span className="px-2.5 py-0.5 rounded text-[10px] font-extrabold bg-amber-500/20 text-amber-300 border border-amber-500/30 uppercase tracking-wider">
                  Personal 1-on-1 Consultation Flow
                </span>
                <h1 className="text-2xl font-extrabold font-serif-title">Handcrafted Custom Designer Cakes</h1>
                <p className="text-xs text-stone-300 max-w-2xl leading-relaxed">
                  Celebrate your unforgettable milestone with a bespoke 3D Barbie Doll, Multi-Tier, or Theme Cake! 
                  Our BAKEBOX Master Chef provides dedicated one-on-one consultation over WhatsApp / Phone to confirm your exact custom weight, flavor profiles, and design feasibility.
                </p>
              </div>
              <div className="bg-white/10 backdrop-blur p-4 rounded-xl border border-white/20 text-center min-w-[200px]">
                <p className="text-xs text-amber-200 font-semibold">Master Baker Hotline</p>
                <p className="text-lg font-extrabold text-white mt-1">+91 9528702189</p>
                <p className="text-[10px] text-stone-300 mt-1">Shri Ram Baker Main Counter</p>
              </div>
            </div>

            {/* Custom Cakes Grid */}
            <div className="grid grid-cols-1 sm:grid-cols-2 md:grid-cols-3 lg:grid-cols-4 gap-6">
              {customCakes.map(cake => (
                <div key={cake.ID} className="bg-white rounded-2xl overflow-hidden border border-amber-200/60 shadow-sm hover:shadow-md transition flex flex-col group">
                  <div className="relative aspect-square overflow-hidden bg-stone-100">
                    <img 
                      src={cake.IMAGE_PATH} 
                      alt={cake.NAME}
                      className="w-full h-full object-cover group-hover:scale-105 transition duration-500"
                      onError={(e) => {
                        e.target.src = 'https://images.unsplash.com/photo-1535141192574-5d4897c13136?w=500&auto=format&fit=crop&q=60';
                      }}
                    />
                    <span className="absolute top-3 left-3 text-[10px] font-extrabold bg-amber-500 text-stone-900 px-2 py-0.5 rounded-full shadow-sm">
                      Designer Theme
                    </span>
                    <span className="absolute bottom-3 right-3 text-[10px] font-bold px-2 py-0.5 rounded bg-white/90 backdrop-blur text-stone-800 shadow">
                      Reference: {cake.WEIGHT_KG} kg
                    </span>
                  </div>

                  <div className="p-4 flex-1 flex flex-col justify-between">
                    <div>
                      <span className="text-[11px] font-bold text-amber-700 uppercase tracking-wide">{cake.FLAVOR}</span>
                      <h3 className="text-sm font-bold text-stone-900 line-clamp-1 mt-1">{cake.NAME}</h3>
                      <p className="text-xs text-stone-500 line-clamp-2 mt-1">{cake.VISUAL_FEATURES || cake.DESCRIPTION}</p>
                      <div className="mt-3 bg-amber-50/80 p-2 rounded-lg border border-amber-100">
                        <p className="text-[10px] font-semibold text-amber-900">
                          <strong>Order Protocol:</strong> {cake.ORDERING_CHANNEL || 'WhatsApp or phone consultation required; baker confirms final weight & quote.'}
                        </p>
                      </div>
                    </div>

                    <div className="mt-4 pt-3 border-t border-stone-100 flex items-center justify-between">
                      <div>
                        <span className="text-[10px] text-stone-400 uppercase">Consultation Quote</span>
                        <p className="text-sm font-bold text-amber-800">Quote by Baker</p>
                      </div>
                      <button
                        onClick={() => {
                          const msg = `Namaste Shri Ram Baker ji! Mujhe ${cake.NAME} (Code: ${cake.DESIGN_CODE}) ke liye 1-on-1 designer cake consultation chahiye.`;
                          window.open(`https://wa.me/919528702189?text=${encodeURIComponent(msg)}`, '_blank');
                        }}
                        className="px-3 py-1.5 bg-emerald-600 hover:bg-emerald-700 text-white text-xs font-bold rounded-xl transition flex items-center gap-1 shadow-sm active:scale-95"
                      >
                        <Phone className="w-3.5 h-3.5" />
                        <span>Book Baker</span>
                      </button>
                    </div>

                  </div>
                </div>
              ))}
            </div>
          </div>
        )}

        {/* Tab 3: Fresh Oven Patties & Raw Bakery items */}
        {activeTab === 'patties' && (
          <div>
            <div className="mb-6 bg-amber-50 border border-amber-200 rounded-2xl p-4 flex items-start gap-3 shadow-sm">
              <AlertTriangle className="w-5 h-5 text-amber-600 flex-shrink-0 mt-0.5" />
              <div>
                <h2 className="text-sm font-bold text-amber-900">Shri Ram Baker Master Reheating Advisory</h2>
                <p className="text-xs text-amber-800 mt-1 leading-relaxed">
                  All patties are fresh oven-baked items with rich flaky puff layers. 
                  <strong> NEVER microwave patties</strong> as moisture ruins the crispness. 
                  Always reheat on a <strong>preheated dry tawa for 2-3 minutes</strong> on medium flame for golden, flaky restaurant-quality puff perfection!
                </p>
              </div>
            </div>

            <div className="grid grid-cols-1 sm:grid-cols-2 md:grid-cols-3 lg:grid-cols-4 gap-6">
              {patties.map(item => (
                <div key={item.SKU_ID} className="bg-white rounded-2xl overflow-hidden border border-stone-200 shadow-sm p-4 flex flex-col justify-between">
                  <div>
                    <div className="flex items-center justify-between">
                      <span className="text-[10px] font-extrabold uppercase px-2 py-0.5 rounded bg-stone-100 text-stone-800">
                        {item.SHAPE}
                      </span>
                      <span className={`text-[10px] font-bold px-2 py-0.5 rounded ${item.IS_EGGLESS === 1 ? 'bg-emerald-100 text-emerald-800' : 'bg-red-100 text-red-800'}`}>
                        {item.IS_EGGLESS === 1 ? '100% Pure Veg' : 'Contains Egg'}
                      </span>
                    </div>

                    <h3 className="text-sm font-bold text-stone-900 mt-2">{item.ITEM_NAME}</h3>
                    <p className="text-xs text-stone-500 mt-1 line-clamp-3">{item.DESCRIPTION}</p>
                    
                    <div className="mt-3 space-y-1 text-[11px] text-stone-600 bg-stone-50 p-2 rounded-lg">
                      <p><strong>Section:</strong> {item.CATEGORY_SECTION}</p>
                      <p><strong>Shelf Life:</strong> {item.SHELF_LIFE_HOURS} Hours</p>
                      <p><strong>Reheat:</strong> Dry Tawa 2-3 Mins</p>
                    </div>
                  </div>

                  <div className="mt-4 pt-3 border-t border-stone-100 flex items-center justify-between">
                    <p className="text-lg font-extrabold text-stone-900">₹{parseFloat(item.PRICE_INR).toFixed(0)}</p>
                    <button
                      onClick={() => addToCart(item)}
                      className="px-3.5 py-1.5 bg-stone-900 hover:bg-amber-600 text-white text-xs font-bold rounded-xl transition flex items-center gap-1.5"
                    >
                      <ShoppingBag className="w-3.5 h-3.5" />
                      <span>Add</span>
                    </button>
                  </div>
                </div>
              ))}
            </div>
          </div>
        )}

        {/* Tab 4: Party Accessories & Snacks */}
        {activeTab === 'snacks' && (
          <div>
            <div className="mb-6 bg-white p-4 rounded-2xl shadow-sm border border-stone-200">
              <h1 className="text-xl font-extrabold text-stone-900 font-serif-title">Party Accessories & Celebration Snacks</h1>
              <p className="text-xs text-stone-500 mt-0.5">Sparklers, musical candles, balloons, party poppers, and quick savories for your Mathura celebration.</p>
            </div>

            <div className="grid grid-cols-1 sm:grid-cols-2 md:grid-cols-3 lg:grid-cols-4 gap-6">
              {accessories.map(item => (
                <div key={item.SKU_ID} className="bg-white rounded-2xl overflow-hidden border border-stone-200 shadow-sm flex flex-col group">
                  <div className="relative aspect-square overflow-hidden bg-stone-100">
                    <img 
                      src={item.IMAGE_PATH} 
                      alt={item.ITEM_NAME}
                      className="w-full h-full object-cover group-hover:scale-105 transition duration-500"
                      onError={(e) => {
                        e.target.src = 'https://images.unsplash.com/photo-1530103862676-de8c9debad1d?w=500&auto=format&fit=crop&q=60';
                      }}
                    />
                    <span className="absolute top-3 left-3 text-[10px] font-extrabold bg-stone-900 text-white px-2 py-0.5 rounded-full">
                      {item.SUB_CATEGORY || item.CATEGORY}
                    </span>
                  </div>

                  <div className="p-4 flex-1 flex flex-col justify-between">
                    <div>
                      <h3 className="text-sm font-bold text-stone-900">{item.ITEM_NAME}</h3>
                      <p className="text-xs text-stone-500 line-clamp-2 mt-1">{item.DESCRIPTION || item.VISUAL_FEATURES}</p>
                      <span className="inline-block mt-2 text-[10px] font-bold text-stone-600 bg-stone-100 px-2 py-0.5 rounded">
                        {item.PACK_SIZE_OR_SERVINGS || 'Standard Pack'}
                      </span>
                    </div>

                    <div className="mt-4 pt-3 border-t border-stone-100 flex items-center justify-between">
                      <p className="text-lg font-extrabold text-stone-900">₹{parseFloat(item.PRICE_INR).toFixed(0)}</p>
                      <button
                        onClick={() => addToCart(item)}
                        className="px-3.5 py-1.5 bg-stone-900 hover:bg-amber-600 text-white text-xs font-bold rounded-xl transition flex items-center gap-1.5"
                      >
                        <ShoppingBag className="w-3.5 h-3.5" />
                        <span>Add</span>
                      </button>
                    </div>
                  </div>
                </div>
              ))}
            </div>
          </div>
        )}

        {/* Tab 5: My Orders */}
        {activeTab === 'orders' && (
          <div>
            <div className="mb-6 bg-white p-4 rounded-2xl shadow-sm border border-stone-200">
              <h1 className="text-xl font-extrabold text-stone-900 font-serif-title">My Orders</h1>
              <p className="text-xs text-stone-500 mt-0.5">Live tracking with Shri Ram Baker's autonomous kitchen queue.</p>
            </div>

            {!user ? (
              <div className="bg-white rounded-2xl p-8 text-center border border-stone-200 max-w-md mx-auto shadow-sm">
                <Shield className="w-10 h-10 text-amber-600 mx-auto mb-3" />
                <h3 className="text-base font-bold text-stone-900">Sign In to Track Orders</h3>
                <p className="text-xs text-stone-500 mt-1 mb-4">Please log in to your BAKEBOX account to review past orders and live preparation updates.</p>
                <button 
                  onClick={() => setShowAuthModal(true)}
                  className="px-4 py-2 bg-stone-900 text-white rounded-xl text-xs font-bold hover:bg-stone-800 transition"
                >
                  Sign In Now
                </button>
              </div>
            ) : myOrders.length === 0 ? (
              <div className="bg-white rounded-2xl p-12 text-center border border-stone-200 text-stone-500">
                <ShoppingBag className="w-12 h-12 text-stone-300 mx-auto mb-2" />
                <p className="text-sm font-bold text-stone-700">No active orders yet.</p>
                <p className="text-xs text-stone-400 mt-1">Explore our fresh cakes and add your favorite celebration treat!</p>
              </div>
            ) : (
              <div className="space-y-4">
                {myOrders.map(order => (
                  <div key={order.order_id} className="bg-white p-5 rounded-2xl border border-stone-200 shadow-sm">
                    <div className="flex flex-col sm:flex-row sm:items-center justify-between gap-2 border-b border-stone-100 pb-3">
                      <div>
                        <span className="text-xs text-stone-400">Order #{order.order_id}</span>
                        <p className="text-sm font-bold text-stone-900 mt-0.5">{order.customer_name} • {order.customer_phone}</p>
                        <p className="text-xs text-stone-500">{order.delivery_address}</p>
                      </div>
                      <div className="sm:text-right">
                        <span className={`inline-block px-2.5 py-1 rounded-full text-xs font-extrabold uppercase ${
                          order.order_status === 'DELIVERED' ? 'bg-emerald-100 text-emerald-800' :
                          order.order_status === 'BAKING' ? 'bg-amber-100 text-amber-800 animate-pulse' :
                          order.order_status === 'READY' ? 'bg-blue-100 text-blue-800' : 'bg-stone-100 text-stone-800'
                        }`}>
                          {order.order_status}
                        </span>
                        <p className="text-base font-extrabold text-stone-900 mt-1">₹{order.total_amount.toFixed(0)}</p>
                      </div>
                    </div>

                    <div className="mt-3 divide-y divide-stone-50">
                      {order.items.map((it, idx) => (
                        <div key={idx} className="py-2 flex items-center justify-between text-xs">
                          <div>
                            <span className="font-bold text-stone-800">{it.ITEM_NAME}</span>
                            <span className="text-stone-400 ml-2">x{it.QUANTITY}</span>
                            {it.CAKE_BASE && (
                              <p className="text-[11px] text-stone-500">Base: {it.CAKE_BASE} | Weight: {it.CAKE_WEIGHT}</p>
                            )}
                          </div>
                          <span className="font-bold text-stone-900">₹{(parseFloat(it.UNIT_PRICE) * it.QUANTITY).toFixed(0)}</span>
                        </div>
                      ))}
                    </div>
                  </div>
                ))}
              </div>
            )}
          </div>
        )}

        {/* Tab 6: Admin Dashboard */}
        {activeTab === 'admin' && user && (user.role === 'ADMIN' || user.role === 'STORE_OPERATOR') && (
          <div className="space-y-6">
            <div className="bg-white p-5 rounded-2xl border border-stone-200 shadow-sm flex flex-col sm:flex-row sm:items-center justify-between gap-4">
              <div>
                <h1 className="text-xl font-extrabold text-stone-900 font-serif-title">BAKEBOX Autonomous Management Console</h1>
                <p className="text-xs text-stone-500 mt-0.5">Connected Instance: IBM Db2 (IBMDB201) • Operators & Kitchen Dispatch</p>
              </div>
              <span className="px-3 py-1 rounded-lg text-xs font-bold bg-amber-100 text-amber-900 border border-amber-200">
                Role: {user.role} ({user.full_name})
              </span>
            </div>

            {/* Metrics Grid */}
            {adminMetrics && (
              <div className="grid grid-cols-2 md:grid-cols-4 gap-4">
                <div className="bg-white p-4 rounded-xl border border-stone-200 shadow-sm">
                  <p className="text-xs font-semibold text-stone-500">Standard Cakes (Db2)</p>
                  <p className="text-2xl font-extrabold text-stone-900 mt-1">{adminMetrics.total_cakes}</p>
                </div>
                <div className="bg-white p-4 rounded-xl border border-stone-200 shadow-sm">
                  <p className="text-xs font-semibold text-stone-500">Designer Cakes (Db2)</p>
                  <p className="text-2xl font-extrabold text-stone-900 mt-1">{adminMetrics.total_custom_cakes}</p>
                </div>
                <div className="bg-white p-4 rounded-xl border border-stone-200 shadow-sm">
                  <p className="text-xs font-semibold text-stone-500">RAG Chunks in IBM Db2</p>
                  <p className="text-2xl font-extrabold text-amber-600 mt-1">{adminMetrics.total_rag_chunks_ibmdb2}</p>
                </div>
                <div className="bg-white p-4 rounded-xl border border-stone-200 shadow-sm">
                  <p className="text-xs font-semibold text-stone-500">Total Revenue</p>
                  <p className="text-2xl font-extrabold text-emerald-600 mt-1">₹{adminMetrics.total_revenue.toFixed(0)}</p>
                </div>
              </div>
            )}

            {/* Family Store Operators */}
            {adminMetrics && adminMetrics.operators && (
              <div className="bg-white p-5 rounded-2xl border border-stone-200 shadow-sm">
                <h2 className="text-sm font-bold text-stone-900 mb-3">Family Store Operators (Mathura Branches)</h2>
                <div className="grid grid-cols-1 md:grid-cols-3 gap-4">
                  {adminMetrics.operators.map(op => (
                    <div key={op.ADMIN_ID} className="p-3 rounded-xl bg-stone-50 border border-stone-200 text-xs space-y-1">
                      <p className="font-bold text-stone-900">{op.OPERATOR_NAME}</p>
                      <p className="text-stone-500">{op.ROLE} • {op.PHONE}</p>
                      <p className="text-amber-800 font-medium">{op.ASSIGNED_BRANCH}</p>
                      <div className="pt-2 flex flex-wrap gap-1 text-[10px]">
                        <span className="px-1.5 py-0.5 rounded bg-emerald-100 text-emerald-800 font-bold">Accept Orders: Yes</span>
                        <span className="px-1.5 py-0.5 rounded bg-blue-100 text-blue-800 font-bold">Toggle Inventory: Yes</span>
                      </div>
                    </div>
                  ))}
                </div>
              </div>
            )}

            {/* Orders Dispatch Queue */}
            <div className="bg-white p-5 rounded-2xl border border-stone-200 shadow-sm">
              <h2 className="text-sm font-bold text-stone-900 mb-3">Live Kitchen Dispatch Queue</h2>
              {adminOrders.length === 0 ? (
                <p className="text-xs text-stone-400 py-4 text-center">No orders currently in queue.</p>
              ) : (
                <div className="divide-y divide-stone-100">
                  {adminOrders.map(order => (
                    <div key={order.order_id} className="py-3 flex flex-col sm:flex-row sm:items-center justify-between gap-3 text-xs">
                      <div>
                        <p className="font-bold text-stone-900">Order #{order.order_id} • {order.customer_name} ({order.customer_phone})</p>
                        <p className="text-stone-500 mt-0.5">{order.delivery_address} • ₹{order.total_amount.toFixed(0)}</p>
                      </div>

                      <div className="flex items-center gap-2">
                        {['CONFIRMED', 'BAKING', 'READY', 'DELIVERED'].map(st => (
                          <button
                            key={st}
                            onClick={async () => {
                              await fetch(`/api/admin/orders/${order.order_id}/status`, {
                                method: 'PATCH',
                                headers: {
                                  'Content-Type': 'application/json',
                                  'Authorization': `Bearer ${token}`
                                },
                                body: JSON.stringify({ status: st })
                              });
                              // Refresh
                              const updated = adminOrders.map(o => o.order_id === order.order_id ? { ...o, order_status: st } : o);
                              setAdminOrders(updated);
                            }}
                            className={`px-2.5 py-1 rounded text-[10px] font-bold transition ${
                              order.order_status === st 
                                ? 'bg-amber-600 text-white shadow-sm' 
                                : 'bg-stone-100 text-stone-600 hover:bg-stone-200'
                            }`}
                          >
                            {st}
                          </button>
                        ))}
                      </div>
                    </div>
                  ))}
                </div>
              )}
            </div>
          </div>
        )}

      </main>

      {/* Cart Drawer */}
      {showCartDrawer && (
        <div className="fixed inset-0 z-50 overflow-hidden bg-black/40 backdrop-blur-sm flex justify-end">
          <div className="w-full max-w-md bg-white h-full shadow-2xl flex flex-col animate-in slide-in-from-right duration-300">
            <div className="p-4 border-b border-stone-200 flex items-center justify-between">
              <div className="flex items-center gap-2">
                <ShoppingBag className="w-5 h-5 text-amber-600" />
                <h2 className="text-base font-bold text-stone-900">Your Fresh Order</h2>
              </div>
              <button onClick={() => setShowCartDrawer(false)} className="p-1 rounded-lg text-stone-400 hover:text-stone-700">
                <X className="w-5 h-5" />
              </button>
            </div>

            <div className="flex-1 overflow-y-auto p-4 space-y-3">
              {cart.length === 0 ? (
                <div className="py-20 text-center text-stone-400">
                  <ShoppingBag className="w-12 h-12 mx-auto mb-2 text-stone-300" />
                  <p className="text-sm font-semibold">Your cart is empty.</p>
                </div>
              ) : (
                cart.map(item => (
                  <div key={item.sku_id} className="p-3 bg-stone-50 rounded-xl border border-stone-200/80 space-y-2">
                    <div className="flex items-start gap-3">
                      <img 
                        src={item.image_url || '/catalog_images/CAKES_BRANDED/ACE/Black Forest/BAKEBOX_ACE_BlackForest_01.jpg'} 
                        alt={item.item_name}
                        className="w-14 h-14 object-cover rounded-xl bg-stone-200 border border-stone-200 flex-shrink-0"
                        onError={(e) => {
                          e.target.src = 'https://images.unsplash.com/photo-1578985545062-69928b1d9587?w=300&auto=format&fit=crop&q=60';
                        }}
                      />
                      <div className="flex-1 min-w-0">
                        <div className="flex items-start justify-between gap-1">
                          <h4 className="text-xs font-bold text-stone-900 line-clamp-1">{item.item_name}</h4>
                          <span className="text-[10px] font-mono text-stone-400 bg-stone-100 px-1 rounded">{item.sku_id}</span>
                        </div>
                        <p className="text-[11px] font-extrabold text-amber-800 mt-0.5">₹{item.unit_price} each</p>

                        <div className="flex items-center justify-between mt-2">
                          {/* Base selection for cakes */}
                          {!item.is_custom ? (
                            <div className="flex items-center gap-1 text-[10px]">
                              <span className="text-stone-500 font-semibold">Base:</span>
                              <select 
                                value={item.cake_base}
                                onChange={e => {
                                  const val = e.target.value;
                                  setCart(prev => prev.map(i => i.sku_id === item.sku_id ? { ...i, cake_base: val } : i));
                                }}
                                className="bg-white border border-stone-200 rounded px-1.5 py-0.5 text-stone-800 font-medium text-[10px]"
                              >
                                <option value="Khoaa (Eggless)">Khoaa (Eggless)</option>
                                <option value="Eggless">Pure Veg Eggless</option>
                                <option value="Chocolate Eggless">Chocolate Eggless</option>
                                <option value="Egg">Egg</option>
                              </select>
                            </div>
                          ) : <div />}

                          <div className="flex items-center gap-2 bg-white px-2 py-1 rounded-lg border border-stone-200">
                            <button onClick={() => updateCartQty(item.sku_id, -1)} className="text-stone-500 hover:text-stone-900">
                              <Minus className="w-3 h-3" />
                            </button>
                            <span className="text-xs font-bold text-stone-800">{item.quantity}</span>
                            <button onClick={() => updateCartQty(item.sku_id, 1)} className="text-stone-500 hover:text-stone-900">
                              <Plus className="w-3 h-3" />
                            </button>
                          </div>
                        </div>

                        {/* Ask CHOCO button for this specific cake */}
                        <button
                          onClick={() => {
                            setShowCartDrawer(false);
                            setShowChocoModal(true);
                            handleSendChoco(`Bhaiya, maine cart mein '${item.item_name}' (SKU: ${item.sku_id}, Base: ${item.cake_base}) add kiya hai. Iske baare mein details bataiye aur iske saath matching party accessories ya candles kya recommend karenge?`);
                          }}
                          className="mt-2 text-[11px] font-bold text-amber-800 hover:text-amber-950 flex items-center gap-1.5 bg-amber-100/70 hover:bg-amber-100 px-2.5 py-1 rounded-lg border border-amber-300/80 transition"
                        >
                          <Sparkles className="w-3.5 h-3.5 text-amber-600" />
                          <span>Ask CHOCO about this cake</span>
                        </button>
                      </div>
                    </div>
                  </div>
                ))
              )}
            </div>

            {cart.length > 0 && (
              <div className="p-4 border-t border-stone-200 bg-stone-50 space-y-3">
                <div className="flex items-center justify-between text-sm">
                  <span className="text-stone-600 font-medium">Estimated Total:</span>
                  <span className="text-xl font-extrabold text-stone-900">₹{cartTotal.toFixed(0)}</span>
                </div>
                
                <input 
                  type="text"
                  placeholder="Delivery Address (Mathura local delivery)"
                  value={deliveryAddress}
                  onChange={e => setDeliveryAddress(e.target.value)}
                  className="w-full px-3 py-2 bg-white border border-stone-200 rounded-xl text-xs text-stone-800 focus:outline-none"
                />

                {/* Ask CHOCO Cart Pairing Button */}
                <button
                  onClick={() => {
                    setShowCartDrawer(false);
                    setShowChocoModal(true);
                    handleSendChoco(`Bhaiya, maine cart mein ${cart.map(c => `${c.item_name} (${c.sku_id})`).join(', ')} add kiya hai. Total ₹${cartTotal.toFixed(0)} hai. Kya aap is celebration ke liye fresh recommendation aur party items pair karna suggest karenge?`);
                  }}
                  className="w-full py-2.5 bg-gradient-to-r from-amber-600 to-orange-600 hover:from-amber-700 hover:to-orange-700 text-white text-xs font-bold rounded-xl transition shadow flex items-center justify-center gap-2 active:scale-95"
                >
                  <Sparkles className="w-4 h-4 text-amber-200 animate-pulse" />
                  <span>Ask CHOCO for Cart Pairing & Recommendations</span>
                </button>

                <button
                  onClick={handleCheckout}
                  className="w-full py-3 bg-stone-900 hover:bg-amber-600 text-white rounded-xl text-xs font-extrabold transition shadow-md active:scale-95"
                >
                  Confirm & Send to Kitchen (3-4 Hrs Wait)
                </button>
              </div>
            )}
          </div>
        </div>
      )}

      {/* Cake Details & Master Baker Advisory Panel Modal */}
      {selectedCakeDetail && (
        <div className="fixed inset-0 z-50 overflow-hidden bg-black/60 backdrop-blur-sm flex items-center justify-center p-4">
          <div className="w-full max-w-lg bg-white rounded-3xl shadow-2xl border border-stone-200 overflow-hidden animate-in zoom-in-95 duration-200">
            {/* Image Header */}
            <div className="relative aspect-video bg-stone-100 overflow-hidden">
              <img 
                src={selectedCakeDetail.IMAGE_PATH} 
                alt={selectedCakeDetail.NAME}
                className="w-full h-full object-cover"
                onError={(e) => {
                  e.target.src = 'https://images.unsplash.com/photo-1578985545062-69928b1d9587?w=600&auto=format&fit=crop&q=60';
                }}
              />
              <button 
                onClick={() => setSelectedCakeDetail(null)}
                className="absolute top-3 right-3 p-2 bg-black/60 hover:bg-black text-white rounded-full transition"
              >
                <X className="w-4 h-4" />
              </button>
              <div className="absolute bottom-3 left-3 flex items-center gap-2">
                <span className="px-2.5 py-1 rounded-full text-[10px] font-extrabold bg-amber-600 text-white shadow">
                  {selectedCakeDetail.CATEGORY}
                </span>
                <span className="px-2.5 py-1 rounded-full text-[10px] font-mono font-bold bg-white/90 backdrop-blur text-stone-800 shadow">
                  SKU: {selectedCakeDetail.SKU_ID}
                </span>
              </div>
            </div>

            {/* Body */}
            <div className="p-6 space-y-4">
              <div>
                <div className="flex items-center justify-between">
                  <span className="text-xs font-bold text-amber-700 uppercase tracking-wider">{selectedCakeDetail.FLAVOR} • {selectedCakeDetail.SUB_CATEGORY}</span>
                  <span className="text-xl font-extrabold text-stone-900">₹{parseFloat(selectedCakeDetail.PRICE).toFixed(0)}</span>
                </div>
                <h3 className="text-base font-extrabold text-stone-900 mt-1">{selectedCakeDetail.NAME}</h3>
                <p className="text-xs text-stone-600 mt-2 leading-relaxed">{selectedCakeDetail.DESCRIPTION || selectedCakeDetail.VISUAL_FEATURES}</p>
              </div>

              {/* Verified Badges */}
              <div className="grid grid-cols-2 gap-2 text-xs">
                <div className="p-2.5 rounded-xl bg-amber-50 border border-amber-200 text-amber-900 flex items-center gap-2">
                  <CheckCircle2 className="w-4 h-4 text-emerald-600 flex-shrink-0" />
                  <span className="text-[11px] font-bold">100% Pure Veg (Khoaa Eggless Available)</span>
                </div>
                <div className="p-2.5 rounded-xl bg-orange-50 border border-orange-200 text-orange-900 flex items-center gap-2">
                  <Clock className="w-4 h-4 text-orange-600 flex-shrink-0" />
                  <span className="text-[11px] font-bold">3-4 Hours Live Fresh Baking</span>
                </div>
              </div>

              {/* Actions */}
              <div className="pt-2 flex items-center gap-3">
                <button
                  onClick={() => {
                    const cake = selectedCakeDetail;
                    setSelectedCakeDetail(null);
                    setShowChocoModal(true);
                    handleSendChoco(`Bhaiya, mujhe is cake '${cake.NAME}' (SKU: ${cake.SKU_ID}, Flavor: ${cake.FLAVOR}, Price: ₹${cake.PRICE}) ke baare mein complete details aur live recommendation bataiye.`);
                  }}
                  className="flex-1 py-3 bg-gradient-to-r from-amber-600 to-orange-600 hover:from-amber-700 hover:to-orange-700 text-white rounded-xl text-xs font-bold transition shadow flex items-center justify-center gap-2 active:scale-95"
                >
                  <Sparkles className="w-4 h-4 text-amber-200" />
                  <span>Ask CHOCO Details</span>
                </button>
                <button
                  onClick={() => {
                    addToCart(selectedCakeDetail);
                    setSelectedCakeDetail(null);
                  }}
                  className="flex-1 py-3 bg-stone-900 hover:bg-stone-800 text-white rounded-xl text-xs font-bold transition shadow flex items-center justify-center gap-2 active:scale-95"
                >
                  <ShoppingBag className="w-4 h-4" />
                  <span>Add to Fresh Cart</span>
                </button>
              </div>
            </div>
          </div>
        </div>
      )}

      {/* CHOCO AI Assistant Interactive Chat Modal (LOCKED BEHIND AUTHENTICATION) */}
      {showChocoModal && (
        <div className="fixed inset-0 z-50 overflow-hidden bg-black/50 backdrop-blur-sm flex items-center justify-center p-4">
          <div className="w-full max-w-2xl bg-white rounded-2xl shadow-2xl border border-stone-200 overflow-hidden flex flex-col h-[650px] animate-in zoom-in-95 duration-200">
            
            {/* Modal Header */}
            <div className="bg-gradient-to-r from-[#2C1810] to-[#1A0E0A] text-white p-4 flex items-center justify-between border-b border-amber-900/40">
              <div className="flex items-center gap-3">
                <div className="w-9 h-9 rounded-xl bg-amber-500/20 border border-amber-400/30 flex items-center justify-center text-amber-300">
                  <Sparkles className="w-5 h-5" />
                </div>
                <div>
                  <div className="flex items-center gap-2">
                    <h3 className="text-sm font-extrabold tracking-wide">CHOCO AI</h3>
                    <span className="px-1.5 py-0.2 rounded text-[10px] bg-amber-400 text-stone-900 font-extrabold">HYBRID RAG</span>
                  </div>
                  <p className="text-[11px] text-amber-200/80">Autonomous Master Baker • Shri Ram Baker, Mathura</p>
                </div>
              </div>

              <div className="flex items-center gap-2">
                {user && (
                  <button 
                    onClick={async () => {
                      await fetch(`/api/choco/history?session_id=user_${user.id}_session`, {
                        method: 'DELETE',
                        headers: { 'Authorization': `Bearer ${token}` }
                      });
                      setChatMessages([{
                        role: 'assistant',
                        content: `Buffer cleared! Radhe Radhe ${user.full_name.split(' ')[0]} ji, kaho kya help karoon?`,
                        ui_cards: []
                      }]);
                    }}
                    className="p-1.5 rounded-lg text-amber-300 hover:text-white hover:bg-white/10 transition"
                    title="Clear Buffer"
                  >
                    <Trash2 className="w-4 h-4" />
                  </button>
                )}
                <button 
                  onClick={() => setShowChocoModal(false)}
                  className="p-1.5 rounded-lg text-amber-300 hover:text-white hover:bg-white/10 transition"
                >
                  <X className="w-5 h-5" />
                </button>
              </div>
            </div>

            {/* Chat Body: Conditional Authentication Lock */}
            {!user ? (
              <div className="flex-1 flex flex-col items-center justify-center p-8 text-center bg-stone-50">
                <div className="w-16 h-16 rounded-2xl bg-amber-100 border border-amber-200 flex items-center justify-center text-amber-700 mb-4 shadow-sm">
                  <Shield className="w-8 h-8" />
                </div>
                <h3 className="text-lg font-extrabold text-stone-900 font-serif-title">CHOCO Assistant is Exclusively Locked</h3>
                <p className="text-xs text-stone-500 max-w-sm mt-2 leading-relaxed">
                  To prevent unauthorized misuse and maintain isolated, secure user conversation buffers, CHOCO AI requires customer login.
                </p>
                <div className="mt-6 flex flex-col sm:flex-row gap-3">
                  <button
                    onClick={() => {
                      setShowChocoModal(false);
                      setAuthMode('login');
                      setShowAuthModal(true);
                    }}
                    className="px-5 py-2.5 bg-stone-900 hover:bg-amber-600 text-white text-xs font-bold rounded-xl transition shadow"
                  >
                    Sign In to Unlock CHOCO
                  </button>
                  <button
                    onClick={() => {
                      setShowChocoModal(false);
                      setAuthMode('register');
                      setShowAuthModal(true);
                    }}
                    className="px-5 py-2.5 bg-white border border-stone-300 text-stone-700 hover:bg-stone-100 text-xs font-bold rounded-xl transition"
                  >
                    Create Account
                  </button>
                </div>
              </div>
            ) : (
              <div className="flex-1 flex flex-col h-full overflow-hidden bg-[#FAF7F2]">
                
                {/* Messages Scroll Area */}
                <div className="flex-1 overflow-y-auto p-4 space-y-4">
                  {chatMessages.map((msg, idx) => (
                    <div 
                      key={idx} 
                      className={`flex flex-col ${msg.role === 'user' ? 'items-end' : 'items-start'}`}
                    >
                      <div className={`max-w-[85%] rounded-2xl p-3.5 text-xs leading-relaxed shadow-sm ${
                        msg.role === 'user' 
                          ? 'bg-amber-600 text-white rounded-br-none' 
                          : 'bg-white text-stone-800 border border-stone-200/80 rounded-bl-none'
                      }`}>
                        <div className="whitespace-pre-line font-medium">{msg.content}</div>

                        {/* Dynamic UI Cards rendered directly inside chat */}
                        {msg.ui_cards && msg.ui_cards.length > 0 && (
                          <div className="mt-3 pt-3 border-t border-stone-100 space-y-2">
                            <span className="text-[10px] font-extrabold uppercase text-amber-700 tracking-wider">
                              Recommended Selection:
                            </span>
                            <div className="grid grid-cols-1 gap-2">
                              {msg.ui_cards.map((card, cIdx) => (
                                <div key={cIdx} className="bg-stone-50 border border-stone-200 rounded-xl p-2.5 flex items-center gap-3">
                                  <img 
                                    src={card.image_url} 
                                    alt={card.name}
                                    className="w-14 h-14 object-cover rounded-lg bg-stone-200 flex-shrink-0"
                                    onError={(e) => {
                                      e.target.src = 'https://images.unsplash.com/photo-1578985545062-69928b1d9587?w=300&auto=format&fit=crop&q=60';
                                    }}
                                  />
                                  <div className="flex-1 min-w-0">
                                    <h4 className="text-xs font-bold text-stone-900 truncate">{card.name}</h4>
                                    <div className="flex items-center gap-1.5 mt-0.5">
                                      <span className="text-[10px] text-stone-500">{card.flavor} • {card.weight_kg}kg</span>
                                      <span className="text-[9px] font-mono text-stone-500 bg-stone-200 px-1 rounded">{card.sku_id}</span>
                                    </div>
                                    <p className="text-xs font-extrabold text-amber-800 mt-0.5">₹{card.price || 249}</p>
                                  </div>
                                  <button
                                    onClick={() => addToCart(card, card.is_custom)}
                                    className="px-2.5 py-1.5 bg-stone-900 hover:bg-amber-600 text-white text-[10px] font-bold rounded-lg transition"
                                  >
                                    Add
                                  </button>
                                </div>
                              ))}
                            </div>
                          </div>
                        )}

                      </div>
                    </div>
                  ))}

                  {chatLoading && (
                    <div className="flex items-center gap-2 text-stone-400 text-xs italic p-2">
                      <Sparkles className="w-4 h-4 text-amber-500 animate-spin" />
                      <span>CHOCO master baker is retrieving catalog & reasoning...</span>
                    </div>
                  )}

                  <div ref={chatBottomRef} />
                </div>

                {/* Quick Suggestion Chips */}
                <div className="p-2 bg-stone-100/70 border-t border-stone-200 flex items-center gap-1.5 overflow-x-auto text-[11px]">
                  {[
                    "Actually I have placed one order, can you provide me the status?",
                    "Anniversary red velvet cake 1kg eggless",
                    "Pineapple 1kg price and base",
                    "Barbie doll custom design booking",
                    "Patties reheating instructions"
                  ].map((chip, idx) => (
                    <button
                      key={idx}
                      onClick={() => handleSendChoco(chip)}
                      className="px-2.5 py-1 rounded-full bg-white border border-stone-200 text-stone-700 hover:text-amber-700 hover:border-amber-400 whitespace-nowrap transition font-medium"
                    >
                      {chip}
                    </button>
                  ))}
                </div>

                {/* Chat Input Bar */}
                <div className="p-3 bg-white border-t border-stone-200 flex items-center gap-2">
                  <input 
                    type="text" 
                    placeholder="Ask CHOCO in Hinglish (e.g. 'Bhaiya 1kg chocolate cake eggless mein milega?')..."
                    value={chatInput}
                    onChange={e => setChatInput(e.target.value)}
                    onKeyDown={e => e.key === 'Enter' && handleSendChoco()}
                    className="flex-1 px-4 py-2 bg-stone-100 border border-stone-200 rounded-xl text-xs text-stone-900 focus:outline-none focus:ring-2 focus:ring-amber-500"
                  />
                  <button
                    onClick={() => handleSendChoco()}
                    disabled={!chatInput.trim() || chatLoading}
                    className="p-2.5 bg-stone-900 hover:bg-amber-600 disabled:opacity-50 text-white rounded-xl transition"
                  >
                    <Send className="w-4 h-4" />
                  </button>
                </div>

              </div>
            )}

          </div>
        </div>
      )}

      {/* Authentication Modal */}
      {showAuthModal && (
        <div className="fixed inset-0 z-50 overflow-hidden bg-black/50 backdrop-blur-sm flex items-center justify-center p-4">
          <div className="w-full max-w-md bg-white rounded-2xl shadow-2xl border border-stone-200 p-6 animate-in zoom-in-95 duration-200">
            <div className="flex items-center justify-between pb-3 border-b border-stone-100">
              <div className="flex items-center gap-2">
                <Shield className="w-5 h-5 text-amber-600" />
                <h3 className="text-base font-bold text-stone-900">
                  {authMode === 'login' ? 'Sign In to BAKEBOX' : 'Create BAKEBOX Account'}
                </h3>
              </div>
              <button onClick={() => setShowAuthModal(false)} className="text-stone-400 hover:text-stone-700">
                <X className="w-5 h-5" />
              </button>
            </div>

            {authError && (
              <div className="mt-3 p-2.5 bg-red-50 text-red-700 text-xs rounded-xl font-medium border border-red-200">
                {authError}
              </div>
            )}

            <form onSubmit={handleAuthSubmit} className="mt-4 space-y-3">
              {authMode === 'register' && (
                <>
                  <div>
                    <label className="text-[11px] font-bold text-stone-700 uppercase">Full Name</label>
                    <input 
                      type="text" 
                      required
                      value={authFullName}
                      onChange={e => setAuthFullName(e.target.value)}
                      placeholder="e.g. Aryan Mathur"
                      className="w-full mt-1 px-3 py-2 bg-stone-100 border border-stone-200 rounded-xl text-xs focus:outline-none focus:ring-2 focus:ring-amber-500"
                    />
                  </div>
                  <div>
                    <label className="text-[11px] font-bold text-stone-700 uppercase">Phone Number</label>
                    <input 
                      type="text" 
                      value={authPhone}
                      onChange={e => setAuthPhone(e.target.value)}
                      placeholder="+91 9876543210"
                      className="w-full mt-1 px-3 py-2 bg-stone-100 border border-stone-200 rounded-xl text-xs focus:outline-none focus:ring-2 focus:ring-amber-500"
                    />
                  </div>
                </>
              )}

              <div>
                <label className="text-[11px] font-bold text-stone-700 uppercase">Email Address</label>
                <input 
                  type="email" 
                  required
                  value={authEmail}
                  onChange={e => setAuthEmail(e.target.value)}
                  placeholder="name@example.com"
                  className="w-full mt-1 px-3 py-2 bg-stone-100 border border-stone-200 rounded-xl text-xs focus:outline-none focus:ring-2 focus:ring-amber-500"
                />
              </div>

              <div>
                <label className="text-[11px] font-bold text-stone-700 uppercase">Password</label>
                <input 
                  type="password" 
                  required
                  value={authPassword}
                  onChange={e => setAuthPassword(e.target.value)}
                  placeholder="••••••••"
                  className="w-full mt-1 px-3 py-2 bg-stone-100 border border-stone-200 rounded-xl text-xs focus:outline-none focus:ring-2 focus:ring-amber-500"
                />
              </div>

              <button
                type="submit"
                className="w-full mt-2 py-2.5 bg-stone-900 hover:bg-amber-600 text-white rounded-xl text-xs font-bold transition shadow"
              >
                {authMode === 'login' ? 'Sign In' : 'Create Account'}
              </button>
            </form>

            {/* Quick Demo Logins */}
            <div className="mt-4 pt-4 border-t border-stone-100">
              <span className="text-[10px] font-extrabold text-stone-400 uppercase tracking-wider block mb-2">
                Quick Demo Credentials:
              </span>
              <div className="grid grid-cols-3 gap-1.5 text-[10px]">
                <button
                  type="button"
                  onClick={() => quickLogin('customer@bakebox.in', 'Customer@123')}
                  className="p-1.5 rounded-lg bg-stone-100 hover:bg-amber-100 text-stone-800 font-bold text-center transition"
                >
                  Customer Demo
                </button>
                <button
                  type="button"
                  onClick={() => quickLogin('admin@bakebox.in', 'Admin@123')}
                  className="p-1.5 rounded-lg bg-red-50 hover:bg-red-100 text-red-900 font-bold text-center transition"
                >
                  Super Admin
                </button>
                <button
                  type="button"
                  onClick={() => quickLogin('operator@bakebox.in', 'Operator@123')}
                  className="p-1.5 rounded-lg bg-blue-50 hover:bg-blue-100 text-blue-900 font-bold text-center transition"
                >
                  Store Operator
                </button>
              </div>
            </div>

            <div className="mt-4 text-center">
              <button
                onClick={() => { setAuthMode(authMode === 'login' ? 'register' : 'login'); setAuthError(''); }}
                className="text-xs text-amber-700 hover:underline font-semibold"
              >
                {authMode === 'login' ? "Don't have an account? Create one" : 'Already have an account? Sign in'}
              </button>
            </div>
          </div>
        </div>
      )}

      {/* Footer */}
      <footer className="bg-stone-900 text-stone-400 text-xs py-8 border-t border-stone-800">
        <div className="max-w-7xl mx-auto px-4 sm:px-6 lg:px-8 flex flex-col md:flex-row items-center justify-between gap-4">
          <div className="space-y-1 text-center md:text-left">
            <p className="font-extrabold text-white text-sm">BAKEBOX Technologies & Retail Platform</p>
            <p className="text-stone-400">Master Baking & Manufacturing Partner: Shri Ram Bakery (Mathura)</p>
            <p className="text-stone-500 text-[11px]">Database: IBM Db2 (Instance IBMDB201) • Autonomous AI: CHOCO (LlamaIndex + Gemini)</p>
          </div>
          <div className="text-center md:text-right text-[11px] text-stone-500">
            <p>© 2026 Shri Ram Baker. All rights reserved.</p>
            <p className="text-amber-400 mt-1">Branch 1: Bhagel Chaupal, Khatoti Kua | Branch 2: Gausna</p>
          </div>
        </div>
      </footer>

    </div>
  );
}
