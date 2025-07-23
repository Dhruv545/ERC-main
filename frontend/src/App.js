import React, { useState, useEffect } from "react";
import "./App.css";
import axios from "axios";

const BACKEND_URL = process.env.REACT_APP_BACKEND_URL;
const API = `${BACKEND_URL}/api`;

function App() {
  const [dashboardData, setDashboardData] = useState(null);
  const [loading, setLoading] = useState(true);
  const [activeTab, setActiveTab] = useState('dashboard');
  
  // Form states
  const [heatForm, setHeatForm] = useState({
    heat_number: '',
    steel_type: '20.64mm',
    quantity_kg: '',
    date_received: new Date().toISOString().split('T')[0]
  });
  
  const [productionForm, setProductionForm] = useState({
    date: new Date().toISOString().split('T')[0],
    product_type: 'MK-III',
    quantity_produced: ''
  });
  
  const [message, setMessage] = useState('');
  const [messageType, setMessageType] = useState('');

  // Fetch dashboard data
  const fetchDashboardData = async () => {
    try {
      setLoading(true);
      const response = await axios.get(`${API}/dashboard`);
      setDashboardData(response.data);
    } catch (error) {
      console.error('Error fetching dashboard data:', error);
      showMessage('Error fetching dashboard data', 'error');
    } finally {
      setLoading(false);
    }
  };

  // Show message
  const showMessage = (msg, type) => {
    setMessage(msg);
    setMessageType(type);
    setTimeout(() => setMessage(''), 5000);
  };

  // Submit heat form
  const submitHeat = async (e) => {
    e.preventDefault();
    try {
      await axios.post(`${API}/heat`, {
        ...heatForm,
        quantity_kg: parseFloat(heatForm.quantity_kg)
      });
      showMessage('Heat added successfully!', 'success');
      setHeatForm({
        heat_number: '',
        steel_type: '20.64mm',
        quantity_kg: '',
        date_received: new Date().toISOString().split('T')[0]
      });
      fetchDashboardData();
    } catch (error) {
      showMessage(error.response?.data?.detail || 'Error adding heat', 'error');
    }
  };

  // Submit production form
  const submitProduction = async (e) => {
    e.preventDefault();
    try {
      await axios.post(`${API}/production`, {
        ...productionForm,
        quantity_produced: parseInt(productionForm.quantity_produced)
      });
      showMessage('Production recorded successfully!', 'success');
      setProductionForm({
        date: new Date().toISOString().split('T')[0],
        product_type: 'MK-III',
        quantity_produced: ''
      });
      fetchDashboardData();
    } catch (error) {
      showMessage(error.response?.data?.detail || 'Error recording production', 'error');
    }
  };

  useEffect(() => {
    fetchDashboardData();
  }, []);

  if (loading) {
    return (
      <div className="min-h-screen bg-gray-50 flex items-center justify-center">
        <div className="text-center">
          <div className="animate-spin rounded-full h-12 w-12 border-b-2 border-blue-600 mx-auto mb-4"></div>
          <p className="text-gray-600">Loading dashboard...</p>
        </div>
      </div>
    );
  }

  return (
    <div className="min-h-screen bg-gray-50">
      {/* Header */}
      <header className="bg-white shadow-sm border-b">
        <div className="max-w-7xl mx-auto px-4 sm:px-6 lg:px-8">
          <div className="flex justify-between items-center h-16">
            <div className="flex items-center">
              <h1 className="text-2xl font-bold text-gray-900">Steel Inventory Dashboard</h1>
              <span className="ml-3 px-2 py-1 text-xs bg-blue-100 text-blue-800 rounded-full">
                Elastic Rail Clips Manufacturing
              </span>
            </div>
            <div className="flex items-center space-x-4">
              <button
                onClick={fetchDashboardData}
                className="px-4 py-2 bg-blue-600 text-white rounded-md hover:bg-blue-700 transition-colors"
              >
                Refresh
              </button>
            </div>
          </div>
        </div>
      </header>

      {/* Message */}
      {message && (
        <div className={`max-w-7xl mx-auto px-4 sm:px-6 lg:px-8 mt-4`}>
          <div className={`p-4 rounded-md ${messageType === 'success' ? 'bg-green-50 text-green-800 border border-green-200' : 'bg-red-50 text-red-800 border border-red-200'}`}>
            {message}
          </div>
        </div>
      )}

      {/* Navigation Tabs */}
      <div className="max-w-7xl mx-auto px-4 sm:px-6 lg:px-8 mt-6">
        <nav className="flex space-x-8">
          {['dashboard', 'add-heat', 'add-production'].map((tab) => (
            <button
              key={tab}
              onClick={() => setActiveTab(tab)}
              className={`py-2 px-1 border-b-2 font-medium text-sm ${
                activeTab === tab
                  ? 'border-blue-500 text-blue-600'
                  : 'border-transparent text-gray-500 hover:text-gray-700 hover:border-gray-300'
              }`}
            >
              {tab === 'dashboard' && 'Dashboard'}
              {tab === 'add-heat' && 'Add Heat'}
              {tab === 'add-production' && 'Record Production'}
            </button>
          ))}
        </nav>
      </div>

      <div className="max-w-7xl mx-auto px-4 sm:px-6 lg:px-8 py-8">
        {/* Dashboard Tab */}
        {activeTab === 'dashboard' && dashboardData && (
          <div className="space-y-6">
            {/* Inventory Status Cards */}
            <div className="grid grid-cols-1 md:grid-cols-2 gap-6">
              {dashboardData.inventory_status.map((inventory, index) => (
                <div key={index} className="bg-white rounded-lg shadow-md p-6 border-l-4 border-blue-500">
                  <div className="flex justify-between items-start mb-4">
                    <div>
                      <h3 className="text-lg font-semibold text-gray-900">{inventory.steel_type} Steel</h3>
                      <p className="text-3xl font-bold text-gray-900 mt-2">{inventory.current_stock_kg.toFixed(1)} kg</p>
                      <p className="text-sm text-gray-600">Current Stock</p>
                    </div>
                    <div className={`px-3 py-1 rounded-full text-sm font-medium ${
                      inventory.low_stock_alert ? 'bg-red-100 text-red-800' : 'bg-green-100 text-green-800'
                    }`}>
                      {inventory.low_stock_alert ? 'Low Stock' : 'Good Stock'}
                    </div>
                  </div>
                  
                  <div className="grid grid-cols-2 gap-4 mb-4">
                    <div>
                      <p className="text-sm text-gray-600">Total Received</p>
                      <p className="text-xl font-semibold text-gray-900">{inventory.total_received_kg.toFixed(1)} kg</p>
                    </div>
                    <div>
                      <p className="text-sm text-gray-600">Total Consumed</p>
                      <p className="text-xl font-semibold text-gray-900">{inventory.total_consumed_kg.toFixed(1)} kg</p>
                    </div>
                  </div>
                  
                  <div className="bg-gray-50 p-3 rounded-md">
                    <p className="text-sm font-medium text-gray-700 mb-1">Reorder Status:</p>
                    <p className={`text-sm ${
                      inventory.reorder_recommendation.includes('URGENT') ? 'text-red-600 font-semibold' :
                      inventory.reorder_recommendation.includes('LOW') ? 'text-yellow-600 font-medium' :
                      'text-green-600'
                    }`}>
                      {inventory.reorder_recommendation}
                    </p>
                  </div>
                </div>
              ))}
            </div>

            {/* Production Summary */}
            <div className="bg-white rounded-lg shadow-md p-6">
              <h3 className="text-lg font-semibold text-gray-900 mb-4">Production Summary</h3>
              <div className="grid grid-cols-1 md:grid-cols-2 gap-6">
                <div className="text-center bg-blue-50 p-4 rounded-lg">
                  <p className="text-3xl font-bold text-blue-600">{dashboardData.total_production_mkiii}</p>
                  <p className="text-sm text-gray-600">Total MK-III Clips</p>
                  <p className="text-xs text-gray-500 mt-1">0.930 kg per clip</p>
                </div>
                <div className="text-center bg-green-50 p-4 rounded-lg">
                  <p className="text-3xl font-bold text-green-600">{dashboardData.total_production_mkv}</p>
                  <p className="text-sm text-gray-600">Total MK-V Clips</p>
                  <p className="text-xs text-gray-500 mt-1">1.15 kg per clip</p>
                </div>
              </div>
            </div>

            {/* Recent Activity */}
            <div className="grid grid-cols-1 lg:grid-cols-2 gap-6">
              {/* Recent Productions */}
              <div className="bg-white rounded-lg shadow-md p-6">
                <h3 className="text-lg font-semibold text-gray-900 mb-4">Recent Productions</h3>
                <div className="space-y-3">
                  {dashboardData.recent_productions.slice(0, 5).map((production, index) => (
                    <div key={index} className="flex justify-between items-center p-3 bg-gray-50 rounded-md">
                      <div>
                        <p className="font-medium text-gray-900">{production.product_type}</p>
                        <p className="text-sm text-gray-600">{production.date}</p>
                      </div>
                      <div className="text-right">
                        <p className="font-semibold text-gray-900">{production.quantity_produced} clips</p>
                        <p className="text-sm text-gray-600">{production.material_consumed_kg.toFixed(2)} kg used</p>
                      </div>
                    </div>
                  ))}
                </div>
              </div>

              {/* Recent Heats */}
              <div className="bg-white rounded-lg shadow-md p-6">
                <h3 className="text-lg font-semibold text-gray-900 mb-4">Recent Heat Additions</h3>
                <div className="space-y-3">
                  {dashboardData.recent_heats.slice(0, 5).map((heat, index) => (
                    <div key={index} className="flex justify-between items-center p-3 bg-gray-50 rounded-md">
                      <div>
                        <p className="font-medium text-gray-900">Heat #{heat.heat_number}</p>
                        <p className="text-sm text-gray-600">{heat.steel_type} - {heat.date_received}</p>
                      </div>
                      <div className="text-right">
                        <p className="font-semibold text-gray-900">{heat.remaining_kg.toFixed(1)} kg</p>
                        <p className="text-sm text-gray-600">remaining</p>
                      </div>
                    </div>
                  ))}
                </div>
              </div>
            </div>
          </div>
        )}

        {/* Add Heat Tab */}
        {activeTab === 'add-heat' && (
          <div className="max-w-md mx-auto bg-white rounded-lg shadow-md p-6">
            <h2 className="text-xl font-semibold text-gray-900 mb-6">Add New Heat</h2>
            <form onSubmit={submitHeat} className="space-y-4">
              <div>
                <label className="block text-sm font-medium text-gray-700 mb-1">Heat Number</label>
                <input
                  type="text"
                  value={heatForm.heat_number}
                  onChange={(e) => setHeatForm({...heatForm, heat_number: e.target.value})}
                  className="w-full px-3 py-2 border border-gray-300 rounded-md focus:outline-none focus:ring-2 focus:ring-blue-500"
                  placeholder="Enter heat number"
                  required
                />
              </div>
              
              <div>
                <label className="block text-sm font-medium text-gray-700 mb-1">Steel Type</label>
                <select
                  value={heatForm.steel_type}
                  onChange={(e) => setHeatForm({...heatForm, steel_type: e.target.value})}
                  className="w-full px-3 py-2 border border-gray-300 rounded-md focus:outline-none focus:ring-2 focus:ring-blue-500"
                >
                  <option value="20.64mm">20.64mm (for MK-III)</option>
                  <option value="23mm">23mm (for MK-V)</option>
                </select>
              </div>
              
              <div>
                <label className="block text-sm font-medium text-gray-700 mb-1">Quantity (kg)</label>
                <input
                  type="number"
                  step="0.1"
                  value={heatForm.quantity_kg}
                  onChange={(e) => setHeatForm({...heatForm, quantity_kg: e.target.value})}
                  className="w-full px-3 py-2 border border-gray-300 rounded-md focus:outline-none focus:ring-2 focus:ring-blue-500"
                  placeholder="Enter quantity in kg"
                  required
                />
              </div>
              
              <div>
                <label className="block text-sm font-medium text-gray-700 mb-1">Date Received</label>
                <input
                  type="date"
                  value={heatForm.date_received}
                  onChange={(e) => setHeatForm({...heatForm, date_received: e.target.value})}
                  className="w-full px-3 py-2 border border-gray-300 rounded-md focus:outline-none focus:ring-2 focus:ring-blue-500"
                  required
                />
              </div>
              
              <button
                type="submit"
                className="w-full bg-blue-600 text-white py-2 px-4 rounded-md hover:bg-blue-700 transition-colors font-medium"
              >
                Add Heat
              </button>
            </form>
          </div>
        )}

        {/* Add Production Tab */}
        {activeTab === 'add-production' && (
          <div className="max-w-md mx-auto bg-white rounded-lg shadow-md p-6">
            <h2 className="text-xl font-semibold text-gray-900 mb-6">Record Production</h2>
            <form onSubmit={submitProduction} className="space-y-4">
              <div>
                <label className="block text-sm font-medium text-gray-700 mb-1">Date</label>
                <input
                  type="date"
                  value={productionForm.date}
                  onChange={(e) => setProductionForm({...productionForm, date: e.target.value})}
                  className="w-full px-3 py-2 border border-gray-300 rounded-md focus:outline-none focus:ring-2 focus:ring-blue-500"
                  required
                />
              </div>
              
              <div>
                <label className="block text-sm font-medium text-gray-700 mb-1">Product Type</label>
                <select
                  value={productionForm.product_type}
                  onChange={(e) => setProductionForm({...productionForm, product_type: e.target.value})}
                  className="w-full px-3 py-2 border border-gray-300 rounded-md focus:outline-none focus:ring-2 focus:ring-blue-500"
                >
                  <option value="MK-III">MK-III (0.930 kg per clip)</option>
                  <option value="MK-V">MK-V (1.15 kg per clip)</option>
                </select>
              </div>
              
              <div>
                <label className="block text-sm font-medium text-gray-700 mb-1">Quantity Produced</label>
                <input
                  type="number"
                  value={productionForm.quantity_produced}
                  onChange={(e) => setProductionForm({...productionForm, quantity_produced: e.target.value})}
                  className="w-full px-3 py-2 border border-gray-300 rounded-md focus:outline-none focus:ring-2 focus:ring-blue-500"
                  placeholder="Enter number of clips produced"
                  required
                />
              </div>
              
              {productionForm.quantity_produced && (
                <div className="bg-gray-50 p-3 rounded-md">
                  <p className="text-sm text-gray-600">Material Required:</p>
                  <p className="text-lg font-semibold text-gray-900">
                    {productionForm.product_type === 'MK-III' 
                      ? (parseInt(productionForm.quantity_produced) * 0.930).toFixed(2)
                      : (parseInt(productionForm.quantity_produced) * 1.15).toFixed(2)} kg
                  </p>
                </div>
              )}
              
              <button
                type="submit"
                className="w-full bg-green-600 text-white py-2 px-4 rounded-md hover:bg-green-700 transition-colors font-medium"
              >
                Record Production
              </button>
            </form>
          </div>
        )}
      </div>
    </div>
  );
}

export default App;