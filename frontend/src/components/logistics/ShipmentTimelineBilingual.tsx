import React from 'react';
import { 
  CheckCircle2, 
  Truck, 
  PackageCheck, 
  Clock, 
  AlertTriangle, 
  MapPin, 
  FileText, 
  UserCircle 
} from 'lucide-react';

// Type definitions matching logistics.py models
interface Location {
  lat?: number;
  lng?: number;
}

export interface ShipmentEvent {
  id: string;
  event_type: string;
  actor: string;
  location_name?: string;
  notes?: string;
  timestamp: string;
  payload?: any;
}

interface ShipmentTimelineProps {
  events: ShipmentEvent[];
  language?: 'en' | 'fa'; // Language support
  loading?: boolean;
}

const getEventConfig = (eventType: string, language: 'en' | 'fa' = 'en') => {
  const configs = {
    en: {
      created: { icon: FileText, color: 'text-gray-500', bgColor: 'bg-gray-100', label: 'Order Created' },
      picked_up_from_factory: { icon: PackageCheck, color: 'text-blue-500', bgColor: 'bg-blue-100', label: 'Picked Up from Factory' },
      assigned_to_carrier: { icon: UserCircle, color: 'text-indigo-500', bgColor: 'bg-indigo-100', label: 'Carrier Assigned' },
      picked_up: { icon: PackageCheck, color: 'text-blue-500', bgColor: 'bg-blue-100', label: 'Picked Up' },
      in_transit: { icon: Truck, color: 'text-purple-500', bgColor: 'bg-purple-100', label: 'In Transit' },
      out_for_delivery: { icon: Truck, color: 'text-purple-500', bgColor: 'bg-purple-100', label: 'Out for Delivery' },
      damaged: { icon: AlertTriangle, color: 'text-red-500', bgColor: 'bg-red-100', label: 'Exception / Issue' },
      failed_delivery: { icon: AlertTriangle, color: 'text-red-500', bgColor: 'bg-red-100', label: 'Failed Delivery' },
      delivered: { icon: CheckCircle2, color: 'text-emerald-500', bgColor: 'bg-emerald-100', label: 'Delivered' },
      telemetry: { icon: MapPin, color: 'text-sky-500', bgColor: 'bg-sky-100', label: 'Location Update' },
      at_customs: { icon: AlertTriangle, color: 'text-orange-500', bgColor: 'bg-orange-100', label: 'At Customs' },
      customs_cleared: { icon: CheckCircle2, color: 'text-green-500', bgColor: 'bg-green-100', label: 'Customs Cleared' },
      at_port: { icon: MapPin, color: 'text-cyan-500', bgColor: 'bg-cyan-100', label: 'At Port' },
      at_warehouse: { icon: PackageCheck, color: 'text-indigo-500', bgColor: 'bg-indigo-100', label: 'At Warehouse' },
    },
    fa: {
      created: { icon: FileText, color: 'text-gray-500', bgColor: 'bg-gray-100', label: 'ثبت سفارش' },
      picked_up_from_factory: { icon: PackageCheck, color: 'text-blue-500', bgColor: 'bg-blue-100', label: 'بارگیری از کارخانه' },
      assigned_to_carrier: { icon: UserCircle, color: 'text-indigo-500', bgColor: 'bg-indigo-100', label: 'تحویل به حمل‌ونقل' },
      picked_up: { icon: PackageCheck, color: 'text-blue-500', bgColor: 'bg-blue-100', label: 'بارگیری شده' },
      in_transit: { icon: Truck, color: 'text-purple-500', bgColor: 'bg-purple-100', label: 'در حال حمل' },
      out_for_delivery: { icon: Truck, color: 'text-purple-500', bgColor: 'bg-purple-100', label: 'در حال تحویل' },
      damaged: { icon: AlertTriangle, color: 'text-red-500', bgColor: 'bg-red-100', label: 'گزارش خسارت' },
      failed_delivery: { icon: AlertTriangle, color: 'text-red-500', bgColor: 'bg-red-100', label: 'تحویل ناموفق' },
      delivered: { icon: CheckCircle2, color: 'text-emerald-500', bgColor: 'bg-emerald-100', label: 'تحویل داده شد' },
      telemetry: { icon: MapPin, color: 'text-sky-500', bgColor: 'bg-sky-100', label: 'بروزرسانی موقعیت' },
      at_customs: { icon: AlertTriangle, color: 'text-orange-500', bgColor: 'bg-orange-100', label: 'در گمرک' },
      customs_cleared: { icon: CheckCircle2, color: 'text-green-500', bgColor: 'bg-green-100', label: 'ترخیص گمرکی' },
      at_port: { icon: MapPin, color: 'text-cyan-500', bgColor: 'bg-cyan-100', label: 'در بندر' },
      at_warehouse: { icon: PackageCheck, color: 'text-indigo-500', bgColor: 'bg-indigo-100', label: 'در انبار' },
    }
  };

  return configs[language][eventType as keyof typeof configs.en] || configs[language].created;
};

const ShipmentTimeline: React.FC<ShipmentTimelineProps> = ({ 
  events, 
  language = 'en',
  loading = false 
}) => {
  const isRTL = language === 'fa';
  const direction = isRTL ? 'rtl' : 'ltr';

  if (loading) {
    return (
      <div className={`w-full max-w-2xl mx-auto p-6 bg-white rounded-2xl shadow-sm border border-gray-100 font-sans`} dir={direction}>
        <div className="animate-pulse">
          <div className="h-6 bg-gray-200 rounded mb-6"></div>
          <div className="space-y-4">
            {[1, 2, 3].map((i) => (
              <div key={i} className="flex items-start space-x-4">
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
    const emptyMessage = language === 'fa' 
      ? 'هیچ رویدادی برای این محموله ثبت نشده است.' 
      : 'No tracking events found for this shipment.';
    
    return (
      <div className={`w-full max-w-2xl mx-auto p-6 bg-white rounded-2xl shadow-sm border border-gray-100 font-sans`} dir={direction}>
        <div className="text-gray-500 text-center py-8 bg-gray-50 rounded-lg border border-gray-200 border-dashed">
          <Clock size={48} className="mx-auto mb-4 text-gray-300" />
          <p>{emptyMessage}</p>
        </div>
      </div>
    );
  }

  const title = language === 'fa' ? 'تاریخچه وضعیت محموله' : 'Tracking History';
  const notesLabel = language === 'fa' ? 'یادداشت‌ها:' : 'Notes:';
  const updatedByLabel = language === 'fa' ? 'ثبت توسط:' : 'Updated by:';

  // Sort events by timestamp
  const sortedEvents = [...events].sort((a, b) => 
    new Date(a.timestamp).getTime() - new Date(b.timestamp).getTime()
  );

  return (
    <div className={`w-full max-w-2xl mx-auto p-6 bg-white rounded-2xl shadow-sm border border-gray-100 font-sans`} dir={direction}>
      <h3 className="text-xl font-bold text-gray-800 mb-8 border-b pb-4">{title}</h3>
      
      <div className={`relative ${isRTL ? 'border-r-2 border-gray-100 mr-4 pr-6' : 'border-l-2 border-gray-100 ml-4 pl-6'}`}>
        {sortedEvents.map((event, index) => {
          const config = getEventConfig(event.event_type, language);
          const Icon = config.icon;
          const isLast = index === sortedEvents.length - 1;
          const eventDate = new Date(event.timestamp);

          return (
            <div key={event.id} className={`relative flex flex-col w-full ${isLast ? '' : 'mb-10'}`}>
              
              {/* Status Icon on the line */}
              <div className={`absolute ${isRTL ? 'right-[-35px]' : '-left-[35px]'} flex items-center justify-center w-8 h-8 rounded-full border-[3px] border-white shadow-sm ${config.bgColor}`}>
                <Icon size={14} className={config.color} />
              </div>

              {/* Event Content */}
              <div className="w-full">
                <div className={`flex flex-col sm:flex-row sm:justify-between sm:items-center mb-1 ${isRTL ? 'text-right' : 'text-left'}`}>
                  <h4 className="font-bold text-gray-900 text-base">
                    {config.label}
                  </h4>
                  <span className="text-xs font-medium text-gray-400 bg-gray-50 px-2 py-1 rounded-md mt-1 sm:mt-0 w-fit">
                    {eventDate.toLocaleString(language === 'fa' ? 'fa-IR' : 'en-US', { 
                      month: 'short', day: 'numeric', 
                      hour: '2-digit', minute: '2-digit' 
                    })}
                  </span>
                </div>
                
                {/* Extra Details Box */}
                {(event.location_name || event.notes || event.actor) && (
                  <div className="mt-3 p-3.5 bg-gray-50/80 rounded-xl text-sm border border-gray-100/80 transition-all hover:bg-gray-50">
                    
                    {event.location_name && (
                      <div className="flex items-center gap-2 mb-2 text-gray-600 font-medium">
                        <MapPin size={14} className="text-gray-400" />
                        <span>{event.location_name}</span>
                      </div>
                    )}
                    
                    {event.notes && (
                      <p className="text-gray-600 mb-2 leading-relaxed">
                        <span className="font-semibold text-gray-700">{notesLabel}</span> {event.notes}
                      </p>
                    )}
                    
                    {event.actor && (
                      <div className={`flex items-center gap-2 text-xs text-gray-400 mt-2 pt-2 border-t border-gray-200/50 ${isRTL ? 'flex-row-reverse' : ''}`}>
                        <UserCircle size={12} />
                        <span>{updatedByLabel} <span className="text-gray-500">{event.actor}</span></span>
                      </div>
                    )}
                  </div>
                )}
              </div>
            </div>
          );
        })}
      </div>
    </div>
  );
};

export default ShipmentTimeline;
