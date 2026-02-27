import { useState, useEffect } from 'react';
import { useRouter } from 'next/navigation';

interface TenantContext {
  tenantId: string;
  language: 'en' | 'fa';
  theme: 'light' | 'dark';
  companyName: string;
  userRole: string;
}

export const useTenantContext = (): TenantContext => {
  const router = useRouter();
  const [context, setContext] = useState<TenantContext>({
    tenantId: '',
    language: 'en',
    theme: 'dark',
    companyName: '',
    userRole: ''
  });

  useEffect(() => {
    // Extract tenant context from JWT token or user preferences
    const extractTenantContext = () => {
      try {
        // Get token from localStorage or cookies
        const token = localStorage.getItem('access_token') || 
                     document.cookie.split('; ').find(row => row.startsWith('access_token='))?.split('=')[1];
        
        if (token) {
          // Decode JWT payload (in production, use proper JWT library)
          const payload = JSON.parse(atob(token.split('.')[1]));
          
          // Determine language based on tenant preferences or user settings
          const tenantLanguage = payload.language || 
                               payload.tenant_language || 
                               (payload.company_name?.includes('فارسی') || payload.company_name?.includes('ایران') ? 'fa' : 'en');
          
          setContext({
            tenantId: payload.tenant_id || payload.current_tenant_id || '',
            language: tenantLanguage as 'en' | 'fa',
            theme: payload.theme || 'dark',
            companyName: payload.company_name || payload.tenant_name || '',
            userRole: payload.role || 'user'
          });
        }
      } catch (error) {
        console.error('Error extracting tenant context:', error);
        // Fallback to English
        setContext(prev => ({ ...prev, language: 'en' }));
      }
    };

    extractTenantContext();
  }, []);

  return context;
};

export default useTenantContext;
