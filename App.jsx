import { useState, useEffect } from 'react'
import { Button } from '@/components/ui/button.jsx'
import { Card, CardContent, CardDescription, CardHeader, CardTitle } from '@/components/ui/card.jsx'
import { Input } from '@/components/ui/input.jsx'
import { Label } from '@/components/ui/label.jsx'
import { Textarea } from '@/components/ui/textarea.jsx'
import { Checkbox } from '@/components/ui/checkbox.jsx'
import { Progress } from '@/components/ui/progress.jsx'
import { Badge } from '@/components/ui/badge.jsx'
import { Tabs, TabsContent, TabsList, TabsTrigger } from '@/components/ui/tabs.jsx'
import { Select, SelectContent, SelectItem, SelectTrigger, SelectValue } from '@/components/ui/select.jsx'
import { 
  Search, 
  Settings, 
  FileText, 
  MessageSquare, 
  Play, 
  Pause, 
  BarChart3,
  Target,
  Briefcase,
  MapPin,
  DollarSign,
  Clock,
  CheckCircle,
  XCircle,
  AlertCircle,
  Terminal
} from 'lucide-react'
import './App.css'

function App() {
  const [activeTab, setActiveTab] = useState('config')
  const [isRunning, setIsRunning] = useState(false)
  const [progress, setProgress] = useState(0)
  const [terminalLogs, setTerminalLogs] = useState([])
  const [credentials, setCredentials] = useState({
    linkedin: { username: '', password: '' },
    infojobs: { username: '', password: '' },
    catho: { username: '', password: '' },
    gupy: { username: '', password: '' }
  })
  const [searchConfig, setSearchConfig] = useState({
    jobTypes: ['Analista financeiro', 'Contas a pagar', 'Contas a receber', 'Analista de precificação', 'Custos'],
    location: 'São Paulo',
    salaryMin: 1900,
    platforms: ['linkedin'],
    modality: 'all',
    requiresEnglish: 'both',
    requiresDegree: 'both'
  })
  const [results, setResults] = useState({
    totalJobs: 0,
    totalApplications: 0,
    platformResults: {},
    jobs: []
  })

  const addLog = (message, type = 'info') => {
    const timestamp = new Date().toLocaleTimeString()
    setTerminalLogs(prev => [...prev, { timestamp, message, type }])
  }

  const handleCredentialChange = (platform, field, value) => {
    setCredentials(prev => ({
      ...prev,
      [platform]: { ...prev[platform], [field]: value }
    }))
  }

  const handleSearchConfigChange = (field, value) => {
    setSearchConfig(prev => ({ ...prev, [field]: value }))
  }

  const handlePlatformToggle = (platform) => {
    setSearchConfig(prev => ({
      ...prev,
      platforms: prev.platforms.includes(platform)
        ? prev.platforms.filter(p => p !== platform)
        : [...prev.platforms, platform]
    }))
  }

  const startAutomation = async () => {
    setIsRunning(true)
    setProgress(0)
    setTerminalLogs([])
    addLog('Iniciando automação JobHunter Pro...', 'success')
    
    try {
      // Simula o processo de automação
      addLog('Configurando credenciais...', 'info')
      setProgress(10)
      
      await new Promise(resolve => setTimeout(resolve, 1000))
      addLog('Conectando às plataformas...', 'info')
      setProgress(25)
      
      await new Promise(resolve => setTimeout(resolve, 1500))
      addLog('Buscando vagas no LinkedIn...', 'info')
      setProgress(50)
      
      await new Promise(resolve => setTimeout(resolve, 2000))
      addLog('Aplicando filtros de busca...', 'info')
      setProgress(75)
      
      await new Promise(resolve => setTimeout(resolve, 1000))
      addLog('Processo concluído com sucesso!', 'success')
      setProgress(100)
      
      // Simula resultados
      setResults({
        totalJobs: 15,
        totalApplications: 8,
        platformResults: {
          linkedin: { jobs: 10, applications: 5 },
          infojobs: { jobs: 3, applications: 2 },
          catho: { jobs: 2, applications: 1 }
        },
        jobs: [
          { id: 1, title: 'Analista Financeiro Jr', company: 'Tech Corp', platform: 'LinkedIn', status: 'applied' },
          { id: 2, title: 'Contas a Pagar', company: 'Finance Ltd', platform: 'Infojobs', status: 'applied' },
          { id: 3, title: 'Analista de Custos', company: 'Industry SA', platform: 'LinkedIn', status: 'found' }
        ]
      })
      
    } catch (error) {
      addLog(`Erro durante a automação: ${error.message}`, 'error')
    } finally {
      setIsRunning(false)
    }
  }

  const stopAutomation = () => {
    setIsRunning(false)
    addLog('Automação interrompida pelo usuário', 'warning')
  }

  return (
    <div className="min-h-screen bg-background text-foreground">
      {/* Header */}
      <header className="border-b border-border bg-card">
        <div className="container mx-auto px-4 py-4">
          <div className="flex items-center justify-between">
            <div className="flex items-center space-x-3">
              <div className="w-10 h-10 bg-primary rounded-lg flex items-center justify-center">
                <Target className="w-6 h-6 text-primary-foreground" />
              </div>
              <div>
                <h1 className="text-2xl font-bold">JobHunter Pro</h1>
                <p className="text-sm text-muted-foreground">Automação Inteligente de Vagas</p>
              </div>
            </div>
            <div className="flex items-center space-x-2">
              {isRunning ? (
                <Button onClick={stopAutomation} variant="destructive" size="sm">
                  <Pause className="w-4 h-4 mr-2" />
                  Parar
                </Button>
              ) : (
                <Button onClick={startAutomation} size="sm">
                  <Play className="w-4 h-4 mr-2" />
                  Iniciar
                </Button>
              )}
            </div>
          </div>
        </div>
      </header>

      <div className="container mx-auto px-4 py-6">
        <Tabs value={activeTab} onValueChange={setActiveTab} className="space-y-6">
          <TabsList className="grid w-full grid-cols-5">
            <TabsTrigger value="config" className="flex items-center space-x-2">
              <Settings className="w-4 h-4" />
              <span>Configuração</span>
            </TabsTrigger>
            <TabsTrigger value="search" className="flex items-center space-x-2">
              <Search className="w-4 h-4" />
              <span>Busca</span>
            </TabsTrigger>
            <TabsTrigger value="results" className="flex items-center space-x-2">
              <BarChart3 className="w-4 h-4" />
              <span>Resultados</span>
            </TabsTrigger>
            <TabsTrigger value="whatsapp" className="flex items-center space-x-2">
              <MessageSquare className="w-4 h-4" />
              <span>WhatsApp</span>
            </TabsTrigger>
            <TabsTrigger value="resume" className="flex items-center space-x-2">
              <FileText className="w-4 h-4" />
              <span>Currículo</span>
            </TabsTrigger>
          </TabsList>

          {/* Configuração de Credenciais */}
          <TabsContent value="config" className="space-y-6">
            <Card>
              <CardHeader>
                <CardTitle>Credenciais das Plataformas</CardTitle>
                <CardDescription>
                  Configure suas credenciais para acesso às plataformas de vagas
                </CardDescription>
              </CardHeader>
              <CardContent className="space-y-6">
                {Object.entries(credentials).map(([platform, creds]) => (
                  <Card key={platform} className="p-4">
                    <div className="flex items-center space-x-3 mb-4">
                      <Briefcase className="w-5 h-5" />
                      <h3 className="font-semibold capitalize">{platform}</h3>
                    </div>
                    <div className="grid grid-cols-2 gap-4">
                      <div>
                        <Label htmlFor={`${platform}-username`}>Email/Usuário</Label>
                        <Input
                          id={`${platform}-username`}
                          type="email"
                          value={creds.username}
                          onChange={(e) => handleCredentialChange(platform, 'username', e.target.value)}
                          placeholder="seu@email.com"
                        />
                      </div>
                      <div>
                        <Label htmlFor={`${platform}-password`}>Senha</Label>
                        <Input
                          id={`${platform}-password`}
                          type="password"
                          value={creds.password}
                          onChange={(e) => handleCredentialChange(platform, 'password', e.target.value)}
                          placeholder="••••••••"
                        />
                      </div>
                    </div>
                  </Card>
                ))}
              </CardContent>
            </Card>
          </TabsContent>

          {/* Configuração de Busca */}
          <TabsContent value="search" className="space-y-6">
            <div className="grid grid-cols-1 lg:grid-cols-2 gap-6">
              <Card>
                <CardHeader>
                  <CardTitle>Critérios de Busca</CardTitle>
                  <CardDescription>
                    Configure os filtros para busca de vagas
                  </CardDescription>
                </CardHeader>
                <CardContent className="space-y-4">
                  <div>
                    <Label htmlFor="location">Localização</Label>
                    <Input
                      id="location"
                      value={searchConfig.location}
                      onChange={(e) => handleSearchConfigChange('location', e.target.value)}
                      placeholder="São Paulo"
                    />
                  </div>
                  
                  <div>
                    <Label htmlFor="salary">Salário Mínimo (R$)</Label>
                    <Input
                      id="salary"
                      type="number"
                      value={searchConfig.salaryMin}
                      onChange={(e) => handleSearchConfigChange('salaryMin', parseInt(e.target.value))}
                      placeholder="1900"
                    />
                  </div>

                  <div>
                    <Label>Modalidade</Label>
                    <Select value={searchConfig.modality} onValueChange={(value) => handleSearchConfigChange('modality', value)}>
                      <SelectTrigger>
                        <SelectValue />
                      </SelectTrigger>
                      <SelectContent>
                        <SelectItem value="all">Todas</SelectItem>
                        <SelectItem value="remote">Remoto</SelectItem>
                        <SelectItem value="hybrid">Híbrido</SelectItem>
                        <SelectItem value="onsite">Presencial</SelectItem>
                      </SelectContent>
                    </Select>
                  </div>
                </CardContent>
              </Card>

              <Card>
                <CardHeader>
                  <CardTitle>Plataformas</CardTitle>
                  <CardDescription>
                    Selecione as plataformas para busca
                  </CardDescription>
                </CardHeader>
                <CardContent className="space-y-4">
                  {['linkedin', 'infojobs', 'catho', 'gupy'].map((platform) => (
                    <div key={platform} className="flex items-center space-x-2">
                      <Checkbox
                        id={platform}
                        checked={searchConfig.platforms.includes(platform)}
                        onCheckedChange={() => handlePlatformToggle(platform)}
                      />
                      <Label htmlFor={platform} className="capitalize">{platform}</Label>
                    </div>
                  ))}
                </CardContent>
              </Card>
            </div>

            <Card>
              <CardHeader>
                <CardTitle>Tipos de Vaga</CardTitle>
                <CardDescription>
                  Tipos de vagas que serão buscadas
                </CardDescription>
              </CardHeader>
              <CardContent>
                <div className="flex flex-wrap gap-2">
                  {searchConfig.jobTypes.map((type, index) => (
                    <Badge key={index} variant="secondary">{type}</Badge>
                  ))}
                </div>
              </CardContent>
            </Card>
          </TabsContent>

          {/* Resultados */}
          <TabsContent value="results" className="space-y-6">
            <div className="grid grid-cols-1 md:grid-cols-3 gap-6">
              <Card>
                <CardHeader className="flex flex-row items-center justify-between space-y-0 pb-2">
                  <CardTitle className="text-sm font-medium">Vagas Encontradas</CardTitle>
                  <Search className="h-4 w-4 text-muted-foreground" />
                </CardHeader>
                <CardContent>
                  <div className="text-2xl font-bold">{results.totalJobs}</div>
                  <p className="text-xs text-muted-foreground">
                    Total de vagas localizadas
                  </p>
                </CardContent>
              </Card>

              <Card>
                <CardHeader className="flex flex-row items-center justify-between space-y-0 pb-2">
                  <CardTitle className="text-sm font-medium">Inscrições Enviadas</CardTitle>
                  <CheckCircle className="h-4 w-4 text-muted-foreground" />
                </CardHeader>
                <CardContent>
                  <div className="text-2xl font-bold">{results.totalApplications}</div>
                  <p className="text-xs text-muted-foreground">
                    Candidaturas realizadas
                  </p>
                </CardContent>
              </Card>

              <Card>
                <CardHeader className="flex flex-row items-center justify-between space-y-0 pb-2">
                  <CardTitle className="text-sm font-medium">Taxa de Sucesso</CardTitle>
                  <BarChart3 className="h-4 w-4 text-muted-foreground" />
                </CardHeader>
                <CardContent>
                  <div className="text-2xl font-bold">
                    {results.totalJobs > 0 ? Math.round((results.totalApplications / results.totalJobs) * 100) : 0}%
                  </div>
                  <p className="text-xs text-muted-foreground">
                    Inscrições vs vagas encontradas
                  </p>
                </CardContent>
              </Card>
            </div>

            {results.jobs.length > 0 && (
              <Card>
                <CardHeader>
                  <CardTitle>Vagas Processadas</CardTitle>
                  <CardDescription>
                    Lista das vagas encontradas e status das inscrições
                  </CardDescription>
                </CardHeader>
                <CardContent>
                  <div className="space-y-4">
                    {results.jobs.map((job) => (
                      <div key={job.id} className="flex items-center justify-between p-4 border border-border rounded-lg">
                        <div className="flex-1">
                          <h3 className="font-semibold">{job.title}</h3>
                          <p className="text-sm text-muted-foreground">{job.company}</p>
                          <Badge variant="outline" className="mt-1">{job.platform}</Badge>
                        </div>
                        <div className="flex items-center space-x-2">
                          {job.status === 'applied' ? (
                            <Badge variant="default" className="bg-green-600">
                              <CheckCircle className="w-3 h-3 mr-1" />
                              Inscrito
                            </Badge>
                          ) : (
                            <Badge variant="secondary">
                              <Clock className="w-3 h-3 mr-1" />
                              Encontrado
                            </Badge>
                          )}
                        </div>
                      </div>
                    ))}
                  </div>
                </CardContent>
              </Card>
            )}
          </TabsContent>

          {/* WhatsApp */}
          <TabsContent value="whatsapp" className="space-y-6">
            <Card>
              <CardHeader>
                <CardTitle>Contato via WhatsApp</CardTitle>
                <CardDescription>
                  Funcionalidade de contato automático com empresas (Em desenvolvimento)
                </CardDescription>
              </CardHeader>
              <CardContent>
                <div className="text-center py-8">
                  <MessageSquare className="w-16 h-16 mx-auto text-muted-foreground mb-4" />
                  <p className="text-muted-foreground">
                    Esta funcionalidade será implementada na próxima versão
                  </p>
                </div>
              </CardContent>
            </Card>
          </TabsContent>

          {/* Análise de Currículo */}
          <TabsContent value="resume" className="space-y-6">
            <Card>
              <CardHeader>
                <CardTitle>Análise de Currículo</CardTitle>
                <CardDescription>
                  Análise e sugestões de melhoria para seu currículo (Em desenvolvimento)
                </CardDescription>
              </CardHeader>
              <CardContent>
                <div className="text-center py-8">
                  <FileText className="w-16 h-16 mx-auto text-muted-foreground mb-4" />
                  <p className="text-muted-foreground">
                    Esta funcionalidade será implementada na próxima versão
                  </p>
                </div>
              </CardContent>
            </Card>
          </TabsContent>
        </Tabs>

        {/* Progress Bar */}
        {isRunning && (
          <Card className="mt-6">
            <CardHeader>
              <CardTitle className="flex items-center space-x-2">
                <Clock className="w-5 h-5" />
                <span>Progresso da Automação</span>
              </CardTitle>
            </CardHeader>
            <CardContent>
              <Progress value={progress} className="w-full" />
              <p className="text-sm text-muted-foreground mt-2">{progress}% concluído</p>
            </CardContent>
          </Card>
        )}

        {/* Terminal */}
        <Card className="mt-6">
          <CardHeader>
            <CardTitle className="flex items-center space-x-2">
              <Terminal className="w-5 h-5" />
              <span>Terminal de Execução</span>
            </CardTitle>
          </CardHeader>
          <CardContent>
            <div className="bg-black rounded-lg p-4 h-64 overflow-y-auto font-mono text-sm">
              {terminalLogs.length === 0 ? (
                <p className="text-green-400">JobHunter Pro v1.0 - Pronto para iniciar...</p>
              ) : (
                terminalLogs.map((log, index) => (
                  <div key={index} className={`mb-1 ${
                    log.type === 'error' ? 'text-red-400' :
                    log.type === 'success' ? 'text-green-400' :
                    log.type === 'warning' ? 'text-yellow-400' :
                    'text-gray-300'
                  }`}>
                    <span className="text-gray-500">[{log.timestamp}]</span> {log.message}
                  </div>
                ))
              )}
            </div>
          </CardContent>
        </Card>
      </div>
    </div>
  )
}

export default App

