import React from 'react';
import { CheckCircle, Truck, Package, Clock, AlertTriangle, MapPin, FileText, Ship, Warehouse, Shield } from 'lucide-react';

// تنظیمات ظاهری (رنگ و آیکون) بر اساس نوع ایونت
const getEventConfig = (eventType) => {
  switch (eventType) {
    case 'created':
      return { icon: FileText, color: 'text-gray-500', bgColor: 'bg-gray-100', label: 'ثبت سفارش' };
    case 'picked_up':
      return { icon: Package, color: 'text-blue-500', bgColor: 'bg-blue-100', label: 'بارگیری از مبدأ' };
    case 'in_transit':
      return { icon: Truck, color: 'text-purple-500', bgColor: 'bg-purple-100', label: 'در حال حمل' };
    case 'at_customs':
      return { icon: Shield, color: 'text-orange-500', bgColor: 'bg-orange-100', label: 'در گمرک' };
    case 'customs_cleared':
      return { icon: CheckCircle, color: 'text-green-500', bgColor: 'bg-green-100', label: 'ترخیص گمرکی' };
    case 'at_port':
      return { icon: Ship, color: 'text-cyan-500', bgColor: 'bg-cyan-100', label: 'در بندر' };
    case 'at_warehouse':
      return { icon: Warehouse, color: 'text-indigo-500', bgColor: 'bg-indigo-100', label: 'در انبار' };
    case 'damaged':
      return { icon: AlertTriangle, color: 'text-red-500', bgColor: 'bg-red-100', label: 'گزارش خسارت' };
    case 'delivered':
      return { icon: CheckCircle, color: 'text-green-600', bgColor: 'bg-green-100', label: 'تحویل داده شد' };
    default:
      return { icon: Clock, color: 'text-gray-400', bgColor: 'bg-gray-50', label: 'در انتظار...' };
  }
};

const ShipmentTimeline = ({ events, loading = false }) => {
  if (loading) {
    return (
      <div className="max-w-md mx-auto p-4 bg-white rounded-2xl shadow-sm border border-gray-100">
        <div className="animate-pulse">
          <div className="h-6 bg-gray-200 rounded mb-6"></div>
          <div className="space-y-4">
            {[1, 2, 3].map((i) => (
              <div key={i} className="flex items-start space-x-4 space-x-reverse">
                <div className="w-8 h-8 bg-gray-200 rounded-full"></div>
                <div className="flex-1">
                  <div className="h-4 bg-gray-200 rounded mb-2"></div>
                  <div className="h-3 bg-gray-100 rounded w-3/4"></div>
                </div>
              </div>
            ))}
          </div>
        </div>
      </div>
    );
  }

  if (!events || events.length === 0) {
    return (
      <div className="max-w-md mx-auto p-4 bg-white rounded-2xl shadow-sm border border-gray-100">
        <div className="text-gray-500 text-center py-8">
          <Clock size={48} className="mx-auto mb-4 text-gray-300" />
          <p>هیچ رویدادی برای این محموله ثبت نشده است.</p>
        </div>
      </div>
    );
  }

  // مرتب‌سازی رویدادها بر اساس زمان
  const sortedEvents = [...events].sort((a, b) => 
    new Date(a.timestamp) - new Date(b.timestamp)
  );

  return (
    <div className="max-w-md mx-auto p-4 bg-white rounded-2xl shadow-sm border border-gray-100">
      <h3 className="text-lg font-bold text-gray-800 mb-6">تاریخچه وضعیت محموله</h3>
      
      <div className="relative border-r-2 border-gray-200 border-opacity-50 pr-4 ml-2 ltr:border-l-0 ltr:border-r-2 ltr:pr-6 ltr:mr-2">
        {sortedEvents.map((event, index) => {
          const config = getEventConfig(event.event_type);
          const Icon = config.icon;
          const isLast = index === sortedEvents.length - 1;

          // استخراج لوکیشن از payload
          const location = event.payload?.location || event.location;

          return (
            <div key={event.id} className={`mb-8 flex items-start w-full ${isLast ? 'mb-0' : ''}`}>
              
              {/* آیکون وضعیت (دایره روی خط) */}
              <div className={`absolute -right-3.5 ltr:-right-3.5 flex items-center justify-center w-8 h-8 rounded-full border-2 border-white shadow-sm ${config.bgColor}`}>
                <Icon size={16} className={config.color} />
              </div>

              {/* محتوای ایونت */}
              <div className="w-full text-right pr-4 ltr:pr-0 ltr:pl-4">
                <div className="flex justify-between items-center mb-1">
                  <h4 className="font-semibold text-gray-800 text-sm md:text-base">
                    {config.label}
                  </h4>
                  <span className="text-xs text-gray-400" dir="ltr">
                    {new Date(event.timestamp).toLocaleTimeString('fa-IR', { 
                      hour: '2-digit', 
                      minute: '2-digit',
                      hour12: false 
                    })}
                    {' - '}
                    {new Date(event.timestamp).toLocaleDateString('fa-IR')}
                  </span>
                </div>
                
                {/* جزئیات تکمیلی مثل لوکیشن یا نوت‌ها */}
                <div className="mt-2 p-3 bg-gray-50 rounded-lg text-sm text-gray-600 border border-gray-100">
                  {location && (
                    <div className="flex items-center gap-1.5 mb-1.5 text-gray-500">
                      <MapPin size={14} />
                      <span>{typeof location === 'string' ? location : location.city || location}</span>
                    </div>
                  )}
                  {event.notes && (
                    <p className="text-gray-700 font-medium">"{event.notes}"</p>
                  )}
                  {event.actor && (
                    <p className="text-xs text-gray-400 mt-2">ثبت توسط: {event.actor}</p>
                  )}
                </div>
              </div>
            </div>
          );
        })}
      </div>
    </div>
  );
};

export default ShipmentTimeline;
