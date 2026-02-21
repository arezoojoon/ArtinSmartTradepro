'use client'

import { useState } from 'react'
import { useRouter } from 'next/navigation'
import { Button } from '@/components/ui/button'
import { Input } from '@/components/ui/input'
import { Label } from '@/components/ui/label'
import { Card, CardContent, CardDescription, CardHeader, CardTitle } from '@/components/ui/card'
import { Select, SelectContent, SelectItem, SelectTrigger, SelectValue } from '@/components/ui/select'
import { Textarea } from '@/components/ui/textarea'
import { ArrowLeft, Plus, Trash2 } from 'lucide-react'
import Link from 'next/link'

interface Identity {
  type: 'email' | 'phone' | 'domain' | 'linkedin' | 'address' | 'other'
  value: string
}

export default function HunterManualLeadPage() {
  const router = useRouter()
  
  const [formData, setFormData] = useState({
    primary_name: '',
    country: '',
    website: '',
    city: '',
    industry: '',
    notes: ''
  })
  
  const [identities, setIdentities] = useState<Identity[]>([])
  const [loading, setLoading] = useState(false)

  const handleInputChange = (field: string, value: string) => {
    setFormData(prev => ({
      ...prev,
      [field]: value
    }))
  }

  const handleAddIdentity = () => {
    setIdentities(prev => [...prev, { type: 'email', value: '' }])
  }

  const handleIdentityChange = (index: number, field: keyof Identity, value: string) => {
    setIdentities(prev => {
      const updated = [...prev]
      updated[index] = { ...updated[index], [field]: value }
      return updated
    })
  }

  const handleRemoveIdentity = (index: number) => {
    setIdentities(prev => prev.filter((_, i) => i !== index))
  }

  const handleSubmit = async (e: React.FormEvent) => {
    e.preventDefault()
    setLoading(true)

    try {
      const payload = {
        primary_name: formData.primary_name,
        country: formData.country,
        website: formData.website || undefined,
        city: formData.city || undefined,
        industry: formData.industry || undefined,
        notes: formData.notes || undefined,
        identities: identities.filter(id => id.value.trim())
      }

      const response = await fetch('/api/hunter/leads/manual', {
        method: 'POST',
        headers: { 'Content-Type': 'application/json' },
        body: JSON.stringify(payload)
      })

      if (!response.ok) {
        const error = await response.json()
        throw new Error(error.detail || 'Failed to create lead')
      }

      router.push('/hunter')
    } catch (error) {
      console.error('Error creating lead:', error)
      alert('Failed to create lead. Please try again.')
    } finally {
      setLoading(false)
    }
  }

  const isFormValid = () => {
    return formData.primary_name.trim() && formData.country.trim()
  }

  return (
    <div className="container mx-auto py-6 max-w-2xl">
      {/* Header */}
      <div className="flex items-center gap-4 mb-6">
        <Button variant="outline" size="sm" asChild>
          <Link href="/hunter">
            <ArrowLeft className="w-4 h-4 mr-2" />
            Back to Hunter
          </Link>
        </Button>
        <div>
          <h1 className="text-2xl font-bold text-gray-900">Add Manual Lead</h1>
          <p className="text-gray-600">Create a new lead manually</p>
        </div>
      </div>

      <form onSubmit={handleSubmit} className="space-y-6">
        {/* Basic Information */}
        <Card>
          <CardHeader>
            <CardTitle>Basic Information</CardTitle>
            <CardDescription>Required lead information</CardDescription>
          </CardHeader>
          <CardContent className="space-y-4">
            <div className="grid grid-cols-1 md:grid-cols-2 gap-4">
              <div>
                <Label htmlFor="primary_name">Company Name *</Label>
                <Input
                  id="primary_name"
                  value={formData.primary_name}
                  onChange={(e) => handleInputChange('primary_name', e.target.value)}
                  placeholder="Enter company name"
                  required
                />
              </div>
              
              <div>
                <Label htmlFor="country">Country *</Label>
                <Select value={formData.country} onValueChange={(value) => handleInputChange('country', value)}>
                  <SelectTrigger>
                    <SelectValue placeholder="Select country" />
                  </SelectTrigger>
                  <SelectContent>
                    <SelectItem value="US">United States</SelectItem>
                    <SelectItem value="CA">Canada</SelectItem>
                    <SelectItem value="GB">United Kingdom</SelectItem>
                    <SelectItem value="DE">Germany</SelectItem>
                    <SelectItem value="FR">France</SelectItem>
                    <SelectItem value="AU">Australia</SelectItem>
                    <SelectItem value="JP">Japan</SelectItem>
                    <SelectItem value="SG">Singapore</SelectItem>
                    <SelectItem value="CN">China</SelectItem>
                    <SelectItem value="IN">India</SelectItem>
                    <SelectItem value="BR">Brazil</SelectItem>
                    <SelectItem value="MX">Mexico</SelectItem>
                    <SelectItem value="KR">South Korea</SelectItem>
                    <SelectItem value="IT">Italy</SelectItem>
                    <SelectItem value="ES">Spain</SelectItem>
                    <SelectItem value="NL">Netherlands</SelectItem>
                    <SelectItem value="SE">Sweden</SelectItem>
                    <SelectItem value="NO">Norway</SelectItem>
                    <SelectItem value="DK">Denmark</SelectItem>
                    <SelectItem value="FI">Finland</SelectItem>
                    <SelectItem value="CH">Switzerland</SelectItem>
                    <SelectItem value="AT">Austria</SelectItem>
                    <SelectItem value="BE">Belgium</SelectItem>
                    <SelectItem value="IE">Ireland</SelectItem>
                    <SelectItem value="PT">Portugal</SelectItem>
                    <SelectItem value="GR">Greece</SelectItem>
                    <SelectItem value="PL">Poland</SelectItem>
                    <SelectItem value="CZ">Czech Republic</SelectItem>
                    <SelectItem value="HU">Hungary</SelectItem>
                    <SelectItem value="RO">Romania</SelectItem>
                    <SelectItem value="BG">Bulgaria</SelectItem>
                    <SelectItem value="HR">Croatia</SelectItem>
                    <SelectItem value="SI">Slovenia</SelectItem>
                    <SelectItem value="SK">Slovakia</SelectItem>
                    <SelectItem value="EE">Estonia</SelectItem>
                    <SelectItem value="LV">Latvia</SelectItem>
                    <SelectItem value="LT">Lithuania</SelectItem>
                    <SelectItem value="RU">Russia</SelectItem>
                    <SelectItem value="TR">Turkey</SelectItem>
                    <SelectItem value="IL">Israel</SelectItem>
                    <SelectItem value="AE">United Arab Emirates</SelectItem>
                    <SelectItem value="SA">Saudi Arabia</SelectItem>
                    <SelectItem value="ZA">South Africa</SelectItem>
                    <SelectItem value="EG">Egypt</SelectItem>
                    <SelectItem value="NG">Nigeria</SelectItem>
                    <SelectItem value="KE">Kenya</SelectItem>
                    <SelectItem value="ZA">South Africa</SelectItem>
                    <SelectItem value="AR">Argentina</SelectItem>
                    <SelectItem value="CL">Chile</SelectItem>
                    <SelectItem value="CO">Colombia</SelectItem>
                    <SelectItem value="PE">Peru</SelectItem>
                    <SelectItem value="VE">Venezuela</SelectItem>
                    <SelectItem value="TH">Thailand</SelectItem>
                    <SelectItem value="VN">Vietnam</SelectItem>
                    <SelectItem value="MY">Malaysia</SelectItem>
                    <SelectItem value="PH">Philippines</SelectItem>
                    <SelectItem value="ID">Indonesia</SelectItem>
                    <SelectItem value="PK">Pakistan</SelectItem>
                    <SelectItem value="BD">Bangladesh</SelectItem>
                    <SelectItem value="LK">Sri Lanka</SelectItem>
                    <SelectItem value="MM">Myanmar</SelectItem>
                    <SelectItem value="KH">Cambodia</SelectItem>
                    <SelectItem value="LA">Laos</SelectItem>
                    <SelectItem value="NP">Nepal</SelectItem>
                    <SelectItem value="BT">Bhutan</SelectItem>
                    <SelectItem value="MN">Mongolia</SelectItem>
                    <SelectItem value="KZ">Kazakhstan</SelectItem>
                    <SelectItem value="UZ">Uzbekistan</SelectItem>
                    <SelectItem value="KG">Kyrgyzstan</SelectItem>
                    <SelectItem value="TJ">Tajikistan</SelectItem>
                    <SelectItem value="TM">Turkmenistan</SelectItem>
                    <SelectItem value="AF">Afghanistan</SelectItem>
                    <SelectItem value="IR">Iran</SelectItem>
                    <SelectItem value="IQ">Iraq</SelectItem>
                    <SelectItem value="SY">Syria</SelectItem>
                    <SelectItem value="LB">Lebanon</SelectItem>
                    <SelectItem value="JO">Jordan</SelectItem>
                    <SelectItem value="PS">Palestine</SelectItem>
                    <SelectItem value="YE">Yemen</SelectItem>
                    <SelectItem value="OM">Oman</SelectItem>
                    <SelectItem value="QA">Qatar</SelectItem>
                    <SelectItem value="BH">Bahrain</SelectItem>
                    <SelectItem value="KW">Kuwait</SelectItem>
                    <SelectItem value="DZ">Algeria</SelectItem>
                    <SelectItem value="TN">Tunisia</SelectItem>
                    <SelectItem value="LY">Libya</SelectItem>
                    <SelectItem value="MA">Morocco</SelectItem>
                    <SelectItem value="SD">Sudan</SelectItem>
                    <SelectItem value="ET">Ethiopia</SelectItem>
                    <SelectItem value="UG">Uganda</SelectItem>
                    <SelectItem value="TZ">Tanzania</SelectItem>
                    <SelectItem value="MW">Malawi</SelectItem>
                    <SelectItem value="ZM">Zambia</SelectItem>
                    <SelectItem value="ZW">Zimbabwe</SelectItem>
                    <SelectItem value="BW">Botswana</SelectItem>
                    <SelectItem value="NA">Namibia</SelectItem>
                    <SelectItem value="SZ">Eswatini</SelectItem>
                    <SelectItem value="LS">Lesotho</SelectItem>
                    <SelectItem value="MG">Madagascar</SelectItem>
                    <SelectItem value="MU">Mauritius</SelectItem>
                    <SelectItem value="SC">Seychelles</SelectItem>
                    <SelectItem value="KM">Comoros</SelectItem>
                    <SelectItem value="CV">Cabo Verde</SelectItem>
                    <SelectItem value="GW">Guinea-Bissau</SelectItem>
                    <SelectItem value="GW">Guinea</SelectItem>
                    <SelectItem value="SL">Sierra Leone</SelectItem>
                    <SelectItem value="LR">Liberia</SelectItem>
                    <SelectItem value="CI">Ivory Coast</SelectItem>
                    <SelectItem value="BF">Burkina Faso</SelectItem>
                    <SelectItem value="ML">Mali</SelectItem>
                    <SelectItem value="NE">Niger</SelectItem>
                    <SelectItem value="TD">Chad</SelectItem>
                    <SelectItem value="CM">Cameroon</SelectItem>
                    <SelectItem value="CF">Central African Republic</SelectItem>
                    <SelectItem value="GA">Gabon</SelectItem>
                    <SelectItem value="CG">Republic of the Congo</SelectItem>
                    <SelectItem value="CD">Democratic Republic of the Congo</SelectItem>
                    <SelectItem value="AO">Angola</SelectItem>
                    <SelectItem value="NA">Namibia</SelectItem>
                    <SelectItem value="MW">Malawi</SelectItem>
                    <SelectItem value="MZ">Mozambique</SelectItem>
                    <SelectItem value="BI">Burundi</SelectItem>
                    <SelectItem value="RW">Rwanda</SelectItem>
                    <SelectItem value="SO">Somalia</SelectItem>
                    <SelectItem value="ER">Eritrea</SelectItem>
                    <SelectItem value="DJ">Djibouti</SelectItem>
                    <SelectItem value="GQ">Equatorial Guinea</SelectItem>
                    <SelectItem value="ST">Sao Tome and Principe</SelectItem>
                    <SelectItem value="GM">The Gambia</SelectItem>
                    <SelectItem value="GN">Guinea</SelectItem>
                    <SelectItem value="GW">Guinea-Bissau</SelectItem>
                  </SelectContent>
                </Select>
              </div>
              
              <div>
                <Label htmlFor="website">Website</Label>
                <Input
                  id="website"
                  type="url"
                  value={formData.website}
                  onChange={(e) => handleInputChange('website', e.target.value)}
                  placeholder="https://example.com"
                />
              </div>
              
              <div>
                <Label htmlFor="city">City</Label>
                <Input
                  id="city"
                  value={formData.city}
                  onChange={(e) => handleInputChange('city', e.target.value)}
                  placeholder="Enter city"
                />
              </div>
              
              <div>
                <Label htmlFor="industry">Industry</Label>
                <Input
                  id="industry"
                  value={formData.industry}
                  onChange={(e) => handleInputChange('industry', e.target.value)}
                  placeholder="e.g., Technology, Manufacturing"
                />
              </div>
            </div>
            
            <div>
              <Label htmlFor="notes">Notes</Label>
              <Textarea
                id="notes"
                value={formData.notes}
                onChange={(e) => handleInputChange('notes', e.target.value)}
                placeholder="Additional notes about this lead..."
                rows={3}
              />
            </div>
          </CardContent>
        </Card>

        {/* Contact Information */}
        <Card>
          <CardHeader>
            <CardTitle>Contact Information</CardTitle>
            <CardDescription>Email, phone, and other contact details</CardDescription>
          </CardHeader>
          <CardContent className="space-y-4">
            {identities.map((identity, index) => (
              <div key={index} className="flex gap-2 items-end">
                <div className="flex-1">
                  <Select
                    value={identity.type}
                    onValueChange={(value) => handleIdentityChange(index, 'type', value as Identity['type'])}
                  >
                    <SelectTrigger>
                      <SelectValue />
                    </SelectTrigger>
                    <SelectContent>
                      <SelectItem value="email">Email</SelectItem>
                      <SelectItem value="phone">Phone</SelectItem>
                      <SelectItem value="domain">Domain</SelectItem>
                      <SelectItem value="linkedin">LinkedIn</SelectItem>
                      <SelectItem value="address">Address</SelectItem>
                      <SelectItem value="other">Other</SelectItem>
                    </SelectContent>
                  </Select>
                </div>
                
                <div className="flex-1">
                  <Input
                    value={identity.value}
                    onChange={(e) => handleIdentityChange(index, 'value', e.target.value)}
                    placeholder={`Enter ${identity.type}...`}
                  />
                </div>
                
                <Button
                  type="button"
                  variant="outline"
                  size="sm"
                  onClick={() => handleRemoveIdentity(index)}
                >
                  <Trash2 className="w-4 h-4" />
                </Button>
              </div>
            ))}
            
            <Button
              type="button"
              variant="outline"
              onClick={handleAddIdentity}
              className="w-full"
            >
              <Plus className="w-4 h-4 mr-2" />
              Add Contact Information
            </Button>
          </CardContent>
        </Card>

        {/* Submit */}
        <div className="flex gap-2">
          <Button
            type="submit"
            disabled={!isFormValid() || loading}
            className="flex-1"
          >
            {loading ? 'Creating...' : 'Create Lead'}
          </Button>
          
          <Button
            type="button"
            variant="outline"
            onClick={() => router.push('/hunter')}
          >
            Cancel
          </Button>
        </div>
      </form>
    </div>
  )
}
