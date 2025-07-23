import React, { useState, useEffect } from "react";
import "./App.css";
import axios from "axios";

const BACKEND_URL = process.env.REACT_APP_BACKEND_URL;
const API = `${BACKEND_URL}/api`;

function App() {
  const [dashboardData, setDashboardData] = useState(null);
  const [loading, setLoading] = useState(true);
  const [activeTab, setActiveTab] = useState('dashboard');
  const [allHeats, setAllHeats] = useState([]);
  const [allProductions, setAllProductions] = useState([]);
  const [editingHeat, setEditingHeat] = useState(null);
  
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

  // Fetch all heats
  const fetchAllHeats = async () => {
    try {
      const response = await axios.get(`${API}/heats`);
      setAllHeats(response.data);
    } catch (error) {
      console.error('Error fetching heats:', error);
      showMessage('Error fetching heats', 'error');
    }
  };

  // Fetch all productions
  const fetchAllProductions = async () => {
    try {
      const response = await axios.get(`${API}/productions`);
      setAllProductions(response.data);
    } catch (error) {
      console.error('Error fetching productions:', error);
      showMessage('Error fetching productions', 'error');
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
      const heatData = {
        ...heatForm,
        quantity_kg: parseFloat(heatForm.quantity_kg)
      };

      if (editingHeat) {
        // Update existing heat
        await axios.put(`${API}/heat/${editingHeat.id}`, heatData);
        showMessage('Heat updated successfully!', 'success');
        setEditingHeat(null);
      } else {
        // Create new heat
        await axios.post(`${API}/heat`, heatData);
        showMessage('Heat added successfully!', 'success');
      }
      
      setHeatForm({
        heat_number: '',
        steel_type: '20.64mm',
        quantity_kg: '',
        date_received: new Date().toISOString().split('T')[0]
      });
      fetchDashboardData();
      fetchAllHeats();
    } catch (error) {
      showMessage(error.response?.data?.detail || 'Error saving heat', 'error');
    }
  };

  // Edit heat
  const editHeat = (heat) => {
    setEditingHeat(heat);
    setHeatForm({
      heat_number: heat.heat_number,
      steel_type: heat.steel_type,
      quantity_kg: heat.quantity_kg.toString(),
      date_received: heat.date_received
    });
    setActiveTab('add-heat');
  };

  // Cancel edit
  const cancelEdit = () => {
    setEditingHeat(null);
    setHeatForm({
      heat_number: '',
      steel_type: '20.64mm',
      quantity_kg: '',
      date_received: new Date().toISOString().split('T')[0]
    });
  };

  // Delete heat
  const deleteHeat = async (heatId) => {
    if (window.confirm('Are you sure you want to delete this heat record?')) {
      try {
        await axios.delete(`${API}/heat/${heatId}`);
        showMessage('Heat deleted successfully!', 'success');
        fetchDashboardData();
        fetchAllHeats();
      } catch (error) {
        showMessage(error.response?.data?.detail || 'Error deleting heat', 'error');
      }
    }
  };

  // Delete production
  const deleteProduction = async (productionId) => {
    if (window.confirm('Are you sure you want to delete this production record? This will restore the consumed material back to inventory.')) {
      try {
        const response = await axios.delete(`${API}/production/${productionId}`);
        const result = response.data;
        showMessage(
          `Production deleted successfully! ${result.material_restored_kg.toFixed(2)}kg restored to inventory.`, 
          'success'
        );
        fetchDashboardData();
        fetchAllProductions();
      } catch (error) {
        showMessage(error.response?.data?.detail || 'Error deleting production', 'error');
      }
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
      fetchAllProductions();
    } catch (error) {
      showMessage(error.response?.data?.detail || 'Error recording production', 'error');
    }
  };

  useEffect(() => {
    fetchDashboardData();
    fetchAllHeats();
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
          {['dashboard', 'add-heat', 'manage-heats', 'add-production'].map((tab) => (
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
              {tab === 'add-heat' && (editingHeat ? 'Edit Heat' : 'Add Heat')}
              {tab === 'manage-heats' && 'Manage Heats'}
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
            <h2 className="text-xl font-semibold text-gray-900 mb-6">
              {editingHeat ? 'Edit Heat Record' : 'Add New Heat'}
            </h2>
            {editingHeat && (
              <div className="mb-4 p-3 bg-blue-50 border border-blue-200 rounded-md">
                <p className="text-sm text-blue-800">
                  Editing Heat: {editingHeat.heat_number} | 
                  Consumed: {(editingHeat.quantity_kg - editingHeat.remaining_kg).toFixed(1)} kg
                </p>
              </div>
            )}
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
              
              <div className="flex space-x-3">
                <button
                  type="submit"
                  className="flex-1 bg-blue-600 text-white py-2 px-4 rounded-md hover:bg-blue-700 transition-colors font-medium"
                >
                  {editingHeat ? 'Update Heat' : 'Add Heat'}
                </button>
                {editingHeat && (
                  <button
                    type="button"
                    onClick={cancelEdit}
                    className="flex-1 bg-gray-600 text-white py-2 px-4 rounded-md hover:bg-gray-700 transition-colors font-medium"
                  >
                    Cancel
                  </button>
                )}
              </div>
            </form>
          </div>
        )}

        {/* Manage Heats Tab */}
        {activeTab === 'manage-heats' && (
          <div className="bg-white rounded-lg shadow-md p-6">
            <h2 className="text-xl font-semibold text-gray-900 mb-6">Manage Heat Records</h2>
            <div className="overflow-x-auto">
              <table className="min-w-full divide-y divide-gray-200">
                <thead className="bg-gray-50">
                  <tr>
                    <th className="px-6 py-3 text-left text-xs font-medium text-gray-500 uppercase tracking-wider">
                      Heat Number
                    </th>
                    <th className="px-6 py-3 text-left text-xs font-medium text-gray-500 uppercase tracking-wider">
                      Steel Type
                    </th>
                    <th className="px-6 py-3 text-left text-xs font-medium text-gray-500 uppercase tracking-wider">
                      Original Qty (kg)
                    </th>
                    <th className="px-6 py-3 text-left text-xs font-medium text-gray-500 uppercase tracking-wider">
                      Remaining (kg)
                    </th>
                    <th className="px-6 py-3 text-left text-xs font-medium text-gray-500 uppercase tracking-wider">
                      Date Received
                    </th>
                    <th className="px-6 py-3 text-left text-xs font-medium text-gray-500 uppercase tracking-wider">
                      Actions
                    </th>
                  </tr>
                </thead>
                <tbody className="bg-white divide-y divide-gray-200">
                  {allHeats.map((heat) => (
                    <tr key={heat.id} className="hover:bg-gray-50">
                      <td className="px-6 py-4 whitespace-nowrap text-sm font-medium text-gray-900">
                        {heat.heat_number}
                      </td>
                      <td className="px-6 py-4 whitespace-nowrap text-sm text-gray-600">
                        {heat.steel_type}
                      </td>
                      <td className="px-6 py-4 whitespace-nowrap text-sm text-gray-600">
                        {heat.quantity_kg.toFixed(1)}
                      </td>
                      <td className="px-6 py-4 whitespace-nowrap text-sm text-gray-600">
                        <span className={`px-2 py-1 rounded-full text-xs font-medium ${
                          heat.remaining_kg > 0 ? 'bg-green-100 text-green-800' : 'bg-red-100 text-red-800'
                        }`}>
                          {heat.remaining_kg.toFixed(1)}
                        </span>
                      </td>
                      <td className="px-6 py-4 whitespace-nowrap text-sm text-gray-600">
                        {heat.date_received}
                      </td>
                      <td className="px-6 py-4 whitespace-nowrap text-sm text-gray-600">
                        <div className="flex space-x-2">
                          <button
                            onClick={() => editHeat(heat)}
                            className="px-3 py-1 bg-blue-600 text-white rounded-md hover:bg-blue-700 transition-colors text-xs"
                          >
                            Edit
                          </button>
                          <button
                            onClick={() => deleteHeat(heat.id)}
                            className="px-3 py-1 bg-red-600 text-white rounded-md hover:bg-red-700 transition-colors text-xs"
                            disabled={heat.remaining_kg < heat.quantity_kg}
                          >
                            Delete
                          </button>
                        </div>
                      </td>
                    </tr>
                  ))}
                </tbody>
              </table>
            </div>
            {allHeats.length === 0 && (
              <div className="text-center py-12">
                <p className="text-gray-500">No heat records found.</p>
              </div>
            )}
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