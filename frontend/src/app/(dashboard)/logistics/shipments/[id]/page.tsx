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
        setError('خطا در دریافت اطلاعات محموله');
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
      <div className="min-h-screen bg-gray-50 p-6" dir="rtl">
        <div className="max-w-6xl mx-auto">
          <div className="animate-pulse">
            <div className="h-8 bg-gray-200 rounded w-1/3 mb-6"></div>
            <div className="grid grid-cols-1 lg:grid-cols-3 gap-6">
              <div className="lg:col-span-2">
                <div className="bg-white rounded-xl p-6 shadow-sm">
                  <div className="h-6 bg-gray-200 rounded mb-4"></div>
                  <div className="space-y-4">
                    {[1, 2, 3].map((i) => (
                      <div key={i} className="h-20 bg-gray-100 rounded"></div>
                    ))}
                  </div>
                </div>
              </div>
              <div>
                <div className="bg-white rounded-xl p-6 shadow-sm">
                  <div className="h-6 bg-gray-200 rounded mb-4"></div>
                  <div className="space-y-3">
                    {[1, 2, 3, 4].map((i) => (
                      <div key={i} className="h-4 bg-gray-100 rounded"></div>
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
      <div className="min-h-screen bg-gray-50 p-6" dir="rtl">
        <div className="max-w-6xl mx-auto">
          <div className="bg-red-50 border border-red-200 rounded-xl p-6 text-center">
            <AlertCircle className="mx-auto mb-4 text-red-500" size={48} />
            <h2 className="text-xl font-bold text-red-800 mb-2">خطا در بارگیری اطلاعات</h2>
            <p className="text-red-600 mb-4">{error || 'محموله مورد نظر یافت نشد'}</p>
            <button
              onClick={() => router.push('/logistics')}
              className="px-4 py-2 bg-red-500 text-white rounded-lg hover:bg-red-600 transition-colors"
            >
              بازگشت به لیست محموله‌ها
            </button>
          </div>
        </div>
      </div>
    );
  }

  const getStatusConfig = (status: string) => {
    switch (status) {
      case 'created':
        return { label: 'ایجاد شده', color: 'bg-gray-100 text-gray-800' };
      case 'picked_up':
        return { label: 'بارگیری شده', color: 'bg-blue-100 text-blue-800' };
      case 'in_transit':
        return { label: 'در حال حمل', color: 'bg-purple-100 text-purple-800' };
      case 'at_customs':
        return { label: 'در گمرک', color: 'bg-orange-100 text-orange-800' };
      case 'delivered':
        return { label: 'تحویل داده شده', color: 'bg-green-100 text-green-800' };
      default:
        return { label: status, color: 'bg-gray-100 text-gray-800' };
    }
  };

  const statusConfig = getStatusConfig(shipment.status);
  const origin = typeof shipment.origin === 'string' ? JSON.parse(shipment.origin) : shipment.origin;
  const destination = typeof shipment.destination === 'string' ? JSON.parse(shipment.destination) : shipment.destination;

  return (
    <div className="min-h-screen bg-gray-50 p-6" dir="rtl">
      <div className="max-w-6xl mx-auto">
        {/* هدر صفحه */}
        <div className="mb-6">
          <button
            onClick={() => router.push('/logistics')}
            className="flex items-center text-gray-600 hover:text-gray-800 mb-4 transition-colors"
          >
            <ArrowRight size={20} className="ml-2" />
            بازگشت به لیست محموله‌ها
          </button>
          
          <div className="flex flex-col md:flex-row md:items-center md:justify-between">
            <div>
              <h1 className="text-2xl font-bold text-gray-800 mb-2">
                محموله {shipment.shipment_number}
              </h1>
              <div className="flex items-center space-x-4 space-x-reverse">
                <span className={`px-3 py-1 rounded-full text-sm font-medium ${statusConfig.color}`}>
                  {statusConfig.label}
                </span>
                <span className="text-sm text-gray-500">
                  {new Date(shipment.created_at).toLocaleDateString('fa-IR')}
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
              language={tenantContext.language}
            />
          </div>

          {/* بخش اطلاعات جانبی */}
          <div className="space-y-6">
            {/* کارت اطلاعات اصلی */}
            <div className="bg-white rounded-xl p-6 shadow-sm">
              <h3 className="text-lg font-bold text-gray-800 mb-4">اطلاعات اصلی</h3>
              
              <div className="space-y-4">
                <div className="flex items-start">
                  <Package className="ml-3 mt-1 text-gray-400" size={20} />
                  <div>
                    <p className="text-sm text-gray-500">نوع کالا</p>
                    <p className="font-medium text-gray-800">{shipment.goods_description}</p>
                  </div>
                </div>

                <div className="flex items-start">
                  <Weight className="ml-3 mt-1 text-gray-400" size={20} />
                  <div>
                    <p className="text-sm text-gray-500">وزن کل</p>
                    <p className="font-medium text-gray-800">{shipment.total_weight_kg?.toLocaleString('fa-IR')} کیلوگرم</p>
                  </div>
                </div>

                <div className="flex items-start">
                  <Package className="ml-3 mt-1 text-gray-400" size={20} />
                  <div>
                    <p className="text-sm text-gray-500">تعداد بسته‌ها</p>
                    <p className="font-medium text-gray-800">{shipment.total_packages} بسته</p>
                  </div>
                </div>

                {shipment.estimated_delivery && (
                  <div className="flex items-start">
                    <Calendar className="ml-3 mt-1 text-gray-400" size={20} />
                    <div>
                      <p className="text-sm text-gray-500">تخمین تحویل</p>
                      <p className="font-medium text-gray-800">
                        {new Date(shipment.estimated_delivery).toLocaleDateString('fa-IR')}
                      </p>
                    </div>
                  </div>
                )}
              </div>
            </div>

            {/* کارت مسیر */}
            <div className="bg-white rounded-xl p-6 shadow-sm">
              <h3 className="text-lg font-bold text-gray-800 mb-4">مسیر حمل</h3>
              
              <div className="space-y-4">
                <div className="flex items-start">
                  <MapPin className="ml-3 mt-1 text-blue-500" size={20} />
                  <div>
                    <p className="text-sm text-gray-500">مبدأ</p>
                    <p className="font-medium text-gray-800">{origin?.city}</p>
                    <p className="text-sm text-gray-600">{origin?.country}</p>
                    {origin?.port && <p className="text-sm text-gray-600">بندر: {origin.port}</p>}
                  </div>
                </div>

                <div className="flex items-center justify-center">
                  <Truck className="text-gray-400" size={20} />
                </div>

                <div className="flex items-start">
                  <MapPin className="ml-3 mt-1 text-green-500" size={20} />
                  <div>
                    <p className="text-sm text-gray-500">مقصد</p>
                    <p className="font-medium text-gray-800">{destination?.city}</p>
                    <p className="text-sm text-gray-600">{destination?.country}</p>
                    {destination?.port && <p className="text-sm text-gray-600">بندر: {destination.port}</p>}
                  </div>
                </div>
              </div>
            </div>

            {/* کارت بسته‌ها */}
            {packages.length > 0 && (
              <div className="bg-white rounded-xl p-6 shadow-sm">
                <h3 className="text-lg font-bold text-gray-800 mb-4">بسته‌ها ({packages.length})</h3>
                
                <div className="space-y-3 max-h-64 overflow-y-auto">
                  {packages.map((pkg) => (
                    <div key={pkg.id} className="flex items-center justify-between p-3 bg-gray-50 rounded-lg">
                      <div className="flex items-center">
                        <Package className="ml-3 text-gray-400" size={16} />
                        <div>
                          <p className="font-medium text-gray-800 text-sm">{pkg.barcode}</p>
                          <p className="text-xs text-gray-500">{pkg.weight_kg} کیلوگرم</p>
                        </div>
                      </div>
                      <span className={`px-2 py-1 rounded-full text-xs font-medium ${
                        pkg.status === 'delivered' ? 'bg-green-100 text-green-800' :
                        pkg.status === 'packed' ? 'bg-blue-100 text-blue-800' :
                        'bg-gray-100 text-gray-800'
                      }`}>
                        {pkg.status === 'delivered' ? 'تحویل شده' :
                         pkg.status === 'packed' ? 'بسته‌بندی شده' : pkg.status}
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
