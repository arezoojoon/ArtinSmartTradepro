"use client";

import React, { useState, useEffect } from 'react';
import { useParams, useRouter } from 'next/navigation';
import { ArrowRight, Package, MapPin, Calendar, Weight, Truck, FileText, AlertCircle } from 'lucide-react';
import ShipmentTimeline from '@/components/logistics/ShipmentTimelineBilingual';
import { api } from '@/lib/api';
import { useTenantContext } from '@/hooks/useTenantContext';

const ShipmentDetailsPage = () => {
  const params = useParams();
  const router = useRouter();
  const tenantContext = useTenantContext();
  const id = params.id as string;
  const [shipment, setShipment] = useState<any>(null);
  const [events, setEvents] = useState<any[]>([]);
  const [packages, setPackages] = useState<any[]>([]);
  const [loading, setLoading] = useState(true);
  const [error, setError] = useState<string | null>(null);

  useEffect(() => {
    const fetchShipmentDetails = async () => {
      try {
        setLoading(true);

        // دریافت اطلاعات محموله
        const shipmentResponse = await api.get(`/logistics/shipments/${id}`);
        setShipment(shipmentResponse.data);

        // دریافت رویدادهای محموله
        const eventsResponse = await api.get(`/logistics/shipments/${id}/events`);
        setEvents(eventsResponse.data);

        // دریافت اطلاعات بسته‌ها
        const packagesResponse = await api.get(`/logistics/shipments/${id}/packages`);
        setPackages(packagesResponse.data);

      } catch (err) {
        console.error('Error fetching shipment details:', err);
        // Error handling
      } finally {
        setLoading(false);
      }
    };

    if (id) {
      fetchShipmentDetails();
    }
  }, [id]);

  if (loading) {
    return (
      <div className="min-h-screen bg-[#050A15] text-slate-300 p-6">
        <div className="max-w-6xl mx-auto">
          <div className="animate-pulse">
            <div className="h-8 bg-slate-800 rounded w-1/3 mb-6"></div>
            <div className="grid grid-cols-1 lg:grid-cols-3 gap-6">
              <div className="lg:col-span-2">
                <div className="bg-slate-900/50 border border-slate-700 rounded-xl p-6 shadow-sm">
                  <div className="h-6 bg-slate-800 rounded mb-4"></div>
                  <div className="space-y-4">
                    {[1, 2, 3].map((i) => (
                      <div key={i} className="h-20 bg-slate-800 rounded"></div>
                    ))}
                  </div>
                </div>
              </div>
              <div>
                <div className="bg-slate-900/50 border border-slate-700 rounded-xl p-6 shadow-sm">
                  <div className="h-6 bg-slate-800 rounded mb-4"></div>
                  <div className="space-y-3">
                    {[1, 2, 3, 4].map((i) => (
                      <div key={i} className="h-4 bg-slate-800 rounded"></div>
                    ))}
                  </div>
                </div>
              </div>
            </div>
          </div>
        </div>
      </div>
    );
  }

  if (error || !shipment) {
    return (
      <div className="min-h-screen bg-[#050A15] p-6 text-slate-300">
        <div className="max-w-6xl mx-auto">
          <div className="bg-red-900/10 border border-red-500/30 rounded-xl p-6 text-center">
            <AlertCircle className="mx-auto mb-4 text-red-500" size={48} />
            <h2 className="text-xl font-bold text-red-400 mb-2">Error Loading Information</h2>
            <p className="text-red-300/80 mb-4">{error || 'Shipment not found'}</p>
            <button
              onClick={() => router.push('/logistics')}
              className="px-4 py-2 bg-red-500/20 text-red-400 border border-red-500/30 rounded-lg hover:bg-red-500/30 transition-colors"
            >
              Back to Shipments
            </button>
          </div>
        </div>
      </div>
    );
  }

  const getStatusConfig = (status: string) => {
    switch (status) {
      case 'created':
        return { label: 'Created', color: 'bg-slate-800 text-slate-300 border-slate-700' };
      case 'picked_up':
        return { label: 'Picked Up', color: 'bg-blue-900/30 text-blue-400 border-blue-500/30' };
      case 'in_transit':
        return { label: 'In Transit', color: 'bg-purple-900/30 text-purple-400 border-purple-500/30' };
      case 'at_customs':
        return { label: 'At Customs', color: 'bg-orange-900/30 text-orange-400 border-orange-500/30' };
      case 'delivered':
        return { label: 'Delivered', color: 'bg-emerald-900/30 text-emerald-400 border-emerald-500/30' };
      default:
        return { label: status, color: 'bg-slate-800 text-slate-300 border-slate-700' };
    }
  };

  const statusConfig = getStatusConfig(shipment.status);
  const origin = typeof shipment.origin === 'string' ? JSON.parse(shipment.origin) : shipment.origin;
  const destination = typeof shipment.destination === 'string' ? JSON.parse(shipment.destination) : shipment.destination;

  return (
    <div className="min-h-screen bg-[#050A15] text-slate-300 p-6">
      <div className="max-w-6xl mx-auto">
        {/* Header */}
        <div className="mb-6">
          <button
            onClick={() => router.push('/logistics')}
            className="flex items-center text-slate-400 hover:text-white mb-4 transition-colors"
          >
            <ArrowRight size={20} className="mr-2 rotate-180" />
            Back to Shipments
          </button>

          <div className="flex flex-col md:flex-row md:items-center md:justify-between">
            <div>
              <h1 className="text-2xl font-bold text-white mb-2">
                Shipment {shipment.shipment_number}
              </h1>
              <div className="flex items-center space-x-4">
                <span className={`px-3 py-1 rounded-full border text-sm font-medium ${statusConfig.color}`}>
                  {statusConfig.label}
                </span>
                <span className="text-sm text-slate-500">
                  {new Date(shipment.created_at).toLocaleDateString()}
                </span>
              </div>
            </div>
          </div>
        </div>

        <div className="grid grid-cols-1 lg:grid-cols-3 gap-6">
          {/* بخش اصلی - تایم‌لاین */}
          <div className="lg:col-span-2">
            <ShipmentTimeline
              events={events}
              loading={loading}
            />
          </div>

          {/* Side Info */}
          <div className="space-y-6">
            {/* Main Info Card */}
            <div className="bg-slate-900/50 border border-slate-700 rounded-xl p-6 shadow-sm">
              <h3 className="text-lg font-bold text-white mb-4">Main Information</h3>

              <div className="space-y-4">
                <div className="flex items-start">
                  <Package className="mr-3 mt-1 text-slate-400" size={20} />
                  <div>
                    <p className="text-sm text-slate-500">Commodity</p>
                    <p className="font-medium text-slate-200">{shipment.goods_description}</p>
                  </div>
                </div>

                <div className="flex items-start">
                  <Weight className="mr-3 mt-1 text-slate-400" size={20} />
                  <div>
                    <p className="text-sm text-slate-500">Total Weight</p>
                    <p className="font-medium text-slate-200">{shipment.total_weight_kg?.toLocaleString()} kg</p>
                  </div>
                </div>

                <div className="flex items-start">
                  <Package className="mr-3 mt-1 text-slate-400" size={20} />
                  <div>
                    <p className="text-sm text-slate-500">Total Packages</p>
                    <p className="font-medium text-slate-200">{shipment.total_packages} package(s)</p>
                  </div>
                </div>

                {shipment.estimated_delivery && (
                  <div className="flex items-start">
                    <Calendar className="mr-3 mt-1 text-slate-400" size={20} />
                    <div>
                      <p className="text-sm text-slate-500">Estimated Delivery</p>
                      <p className="font-medium text-slate-200">
                        {new Date(shipment.estimated_delivery).toLocaleDateString()}
                      </p>
                    </div>
                  </div>
                )}
              </div>
            </div>

            {/* Route Card */}
            <div className="bg-slate-900/50 border border-slate-700 rounded-xl p-6 shadow-sm">
              <h3 className="text-lg font-bold text-white mb-4">Route Info</h3>

              <div className="space-y-4">
                <div className="flex items-start">
                  <MapPin className="mr-3 mt-1 text-blue-500" size={20} />
                  <div>
                    <p className="text-sm text-slate-500">Origin</p>
                    <p className="font-medium text-slate-200">{origin?.city}</p>
                    <p className="text-sm text-slate-400">{origin?.country}</p>
                    {origin?.port && <p className="text-sm text-slate-400">Port: {origin.port}</p>}
                  </div>
                </div>

                <div className="flex items-center justify-center">
                  <Truck className="text-slate-600" size={20} />
                </div>

                <div className="flex items-start">
                  <MapPin className="mr-3 mt-1 text-emerald-500" size={20} />
                  <div>
                    <p className="text-sm text-slate-500">Destination</p>
                    <p className="font-medium text-slate-200">{destination?.city}</p>
                    <p className="text-sm text-slate-400">{destination?.country}</p>
                    {destination?.port && <p className="text-sm text-slate-400">Port: {destination.port}</p>}
                  </div>
                </div>
              </div>
            </div>

            {/* Packages Card */}
            {packages.length > 0 && (
              <div className="bg-slate-900/50 border border-slate-700 rounded-xl p-6 shadow-sm">
                <h3 className="text-lg font-bold text-white mb-4">Packages ({packages.length})</h3>

                <div className="space-y-3 max-h-64 overflow-y-auto custom-scrollbar pr-2">
                  {packages.map((pkg) => (
                    <div key={pkg.id} className="flex items-center justify-between p-3 bg-slate-800/50 border border-slate-700 rounded-lg">
                      <div className="flex items-center">
                        <Package className="mr-3 text-[#D4AF37]" size={16} />
                        <div>
                          <p className="font-medium text-slate-200 text-sm">{pkg.barcode}</p>
                          <p className="text-xs text-slate-400">{pkg.weight_kg} kg</p>
                        </div>
                      </div>
                      <span className={`px-2 py-1 rounded-full text-xs font-medium border ${pkg.status === 'delivered' ? 'bg-emerald-900/30 text-emerald-400 border-emerald-500/30' :
                        pkg.status === 'packed' ? 'bg-blue-900/30 text-blue-400 border-blue-500/30' :
                          'bg-slate-800 text-slate-300 border-slate-700'
                        }`}>
                        {pkg.status === 'delivered' ? 'Delivered' :
                          pkg.status === 'packed' ? 'Packed' : pkg.status}
                      </span>
                    </div>
                  ))}
                </div>
              </div>
            )}
          </div>
        </div>
      </div>
    </div>
  );
};

export default ShipmentDetailsPage;
