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
  actor?: string;
  location_name?: string;
  notes?: string;
  timestamp: string;
  payload?: any;
}

interface ShipmentTimelineProps {
  events: ShipmentEvent[];
  loading?: boolean;
}

const getEventConfig = (eventType: string) => {
  const configs = {
    created: { icon: FileText, color: 'text-slate-400', bgColor: 'bg-navy-800', borderColor: 'border-slate-500/50', label: 'Order Created' },
    picked_up_from_factory: { icon: PackageCheck, color: 'text-blue-400', bgColor: 'bg-blue-900/30', borderColor: 'border-blue-500/50', label: 'Picked Up from Factory' },
    assigned_to_carrier: { icon: UserCircle, color: 'text-indigo-400', bgColor: 'bg-indigo-900/30', borderColor: 'border-indigo-500/50', label: 'Carrier Assigned' },
    picked_up: { icon: PackageCheck, color: 'text-blue-400', bgColor: 'bg-blue-900/30', borderColor: 'border-blue-500/50', label: 'Picked Up' },
    in_transit: { icon: Truck, color: 'text-purple-400', bgColor: 'bg-purple-900/30', borderColor: 'border-purple-500/50', label: 'In Transit' },
    out_for_delivery: { icon: Truck, color: 'text-purple-400', bgColor: 'bg-purple-900/30', borderColor: 'border-purple-500/50', label: 'Out for Delivery' },
    damaged: { icon: AlertTriangle, color: 'text-red-400', bgColor: 'bg-red-900/30', borderColor: 'border-red-500/50', label: 'Exception / Issue' },
    failed_delivery: { icon: AlertTriangle, color: 'text-red-400', bgColor: 'bg-red-900/30', borderColor: 'border-red-500/50', label: 'Failed Delivery' },
    delivered: { icon: CheckCircle2, color: 'text-emerald-400', bgColor: 'bg-emerald-900/30', borderColor: 'border-emerald-500/50', label: 'Delivered' },
    telemetry: { icon: MapPin, color: 'text-gold-400', bgColor: 'bg-gold-900/30', borderColor: 'border-gold-500/50', label: 'Location Update' },
    at_customs: { icon: AlertTriangle, color: 'text-orange-400', bgColor: 'bg-orange-900/30', borderColor: 'border-orange-500/50', label: 'At Customs' },
    customs_cleared: { icon: CheckCircle2, color: 'text-emerald-400', bgColor: 'bg-emerald-900/30', borderColor: 'border-emerald-500/50', label: 'Customs Cleared' },
    at_port: { icon: MapPin, color: 'text-cyan-400', bgColor: 'bg-cyan-900/30', borderColor: 'border-cyan-500/50', label: 'At Port' },
    at_warehouse: { icon: PackageCheck, color: 'text-indigo-400', bgColor: 'bg-indigo-900/30', borderColor: 'border-indigo-500/50', label: 'At Warehouse' },
  };

  return configs[eventType as keyof typeof configs] || configs.created;
};

const ShipmentTimeline: React.FC<ShipmentTimelineProps> = ({
  events,
  loading = false
}) => {
  if (loading) {
    return (
      <div className="w-full max-w-2xl mx-auto p-6 bg-navy-900 rounded-2xl shadow-[0_4px_24px_rgba(251,191,36,0.05)] border border-white/10 font-sans" dir="ltr">
        <div className="animate-pulse">
          <div className="h-6 bg-white/10 rounded mb-6 w-1/3"></div>
          <div className="space-y-6">
            {[1, 2, 3].map((i) => (
              <div key={i} className="flex items-start space-x-4">
                <div className="w-8 h-8 bg-white/10 rounded-full shrink-0"></div>
                <div className="flex-1">
                  <div className="h-4 bg-white/10 rounded mb-3 w-1/4"></div>
                  <div className="h-20 bg-white/5 rounded-xl w-full"></div>
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
      <div className="w-full max-w-2xl mx-auto p-6 bg-navy-900 rounded-2xl shadow-[0_4px_24px_rgba(251,191,36,0.05)] border border-white/10 font-sans" dir="ltr">
        <div className="text-slate-400 text-center py-8 bg-navy-950/50 rounded-lg border border-white/10 border-dashed">
          <Clock size={48} className="mx-auto mb-4 text-slate-500/50" />
          <p>No tracking events found for this shipment.</p>
        </div>
      </div>
    );
  }

  // Sort events by timestamp
  const sortedEvents = [...events].sort((a, b) =>
    new Date(a.timestamp).getTime() - new Date(b.timestamp).getTime()
  );

  return (
    <div className="w-full max-w-2xl mx-auto p-6 bg-navy-900 rounded-2xl shadow-[0_4px_24px_rgba(251,191,36,0.05)] border border-white/10 font-sans" dir="ltr">
      <h3 className="text-xl font-bold text-white mb-8 border-b border-white/10 pb-4">Tracking History</h3>

      <div className="relative border-l-2 border-white/10 ml-4 pl-8">
        {sortedEvents.map((event, index) => {
          const config = getEventConfig(event.event_type);
          const Icon = config.icon;
          const isLast = index === sortedEvents.length - 1;
          const eventDate = new Date(event.timestamp);

          return (
            <div key={event.id} className={`relative flex flex-col w-full ${isLast ? '' : 'mb-10'}`}>

              {/* Status Icon on the line */}
              <div className={`absolute -left-[49px] flex items-center justify-center w-8 h-8 rounded-full border-[2px] shadow-sm ${config.bgColor} ${config.borderColor}`}>
                <Icon size={14} className={config.color} />
              </div>

              {/* Event Content */}
              <div className="w-full">
                <div className="flex flex-col sm:flex-row sm:justify-between sm:items-center mb-2 text-left">
                  <h4 className="font-bold text-slate-100 text-base">
                    {config.label}
                  </h4>
                  <span className="text-xs font-medium text-slate-400 bg-navy-800 border border-white/5 px-2.5 py-1 rounded-md mt-2 sm:mt-0 w-fit">
                    {eventDate.toLocaleString('en-US', {
                      month: 'short', day: 'numeric',
                      hour: '2-digit', minute: '2-digit'
                    })}
                  </span>
                </div>

                {/* Extra Details Box */}
                {(event.location_name || event.notes || event.actor) && (
                  <div className="mt-2.5 p-4 bg-navy-800/80 rounded-xl text-sm border border-white/5 transition-all hover:bg-navy-800">

                    {event.location_name && (
                      <div className="flex items-center gap-2 mb-2.5 text-slate-300 font-medium">
                        <MapPin size={14} className="text-gold-400" />
                        <span>{event.location_name}</span>
                      </div>
                    )}

                    {event.notes && (
                      <p className="text-slate-300 mb-2 leading-relaxed">
                        <span className="font-semibold text-slate-400">Notes:</span> {event.notes}
                      </p>
                    )}

                    {event.actor && (
                      <div className="flex items-center gap-2 text-xs text-slate-400 mt-3 pt-3 border-t border-white/5">
                        <UserCircle size={14} className="text-slate-500" />
                        <span>Updated by: <span className="text-slate-300">{event.actor}</span></span>
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
