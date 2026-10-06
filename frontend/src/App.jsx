import { useCallback, useEffect, useMemo, useState } from 'react'
import {
  Bar,
  BarChart,
  CartesianGrid,
  Cell,
  Pie,
  PieChart,
  ResponsiveContainer,
  Tooltip,
  XAxis,
  YAxis,
} from 'recharts'
import './App.css'

const API_BASE_URL = import.meta.env.VITE_API_BASE_URL || 'http://localhost:8000'
const CHART_COLORS = ['#315f54', '#d7955b', '#6d8eaa', '#a6b98c', '#bd7a68', '#8780a8']
const EMPTY_FILTERS = {
  city: '',
  weather: '',
  traffic: '',
  vehicle: '',
  festival: '',
  order_type: '',
}

const chartDefinitions = [
  { key: 'orders_by_city', title: 'Orders by City', labelKey: 'city', valueKey: 'total_orders', unit: 'orders', color: '#315f54', type: 'bar' },
  { key: 'orders_by_traffic', title: 'Orders by Traffic Density', labelKey: 'traffic_density', valueKey: 'total_orders', unit: 'orders', color: '#d7955b', type: 'bar' },
  { key: 'orders_by_weather', title: 'Orders by Weather', labelKey: 'weather', valueKey: 'total_orders', unit: 'orders', color: '#6d8eaa', type: 'pie' },
  { key: 'orders_by_vehicle', title: 'Orders by Vehicle Type', labelKey: 'vehicle_type', valueKey: 'total_orders', unit: 'orders', color: '#a6b98c', type: 'pie' },
  { key: 'orders_by_festival', title: 'Orders by Festival', labelKey: 'festival', valueKey: 'total_orders', unit: 'orders', color: '#bd7a68', type: 'bar' },
  { key: 'distance_by_city', title: 'Average Delivery Distance by City', labelKey: 'city', valueKey: 'average_distance_km', unit: 'km', color: '#8780a8', type: 'bar' },
]

async function fetchJson(path, options = {}) {
  const response = await fetch(`${API_BASE_URL}${path}`, options)
  if (!response.ok) {
    const errorBody = await response.json().catch(() => null)
    const message = errorBody?.detail || `Request failed (${response.status})`
    throw new Error(message)
  }
  return response.json()
}

function getRows(data) {
  return Array.isArray(data) ? data : []
}

function formatNumber(value, decimals = 0) {
  if (value == null || value === '') return '—'
  const number = Number(value)
  if (!Number.isFinite(number)) return '—'
  return number.toLocaleString(undefined, {
    minimumFractionDigits: decimals,
    maximumFractionDigits: decimals,
  })
}

function ChartTooltip({ active, payload, label, unit = 'orders' }) {
  if (!active || !payload?.length) return null
  const name = label || payload[0].name
  const val = payload[0].value
  return (
    <div className="chart-tooltip">
      <span>{name}</span>
      <strong>{formatNumber(val, unit === 'km' ? 2 : 0)} {unit}</strong>
    </div>
  )
}

function ChartCard({ definition, data, loading }) {
  const rows = getRows(data)
  const chartData = rows.map((row) => ({
    name: row[definition.labelKey] || 'Unknown',
    value: Number(row[definition.valueKey || 'total_orders']) || 0,
  }))
  const isWide = definition.key === 'orders_by_city' || definition.key === 'distance_by_city'

  return (
    <section className={`chart-card${isWide ? ' chart-card-wide' : ''}`}>
      <div className="card-heading">
        <div>
          <h2>{definition.title}</h2>
          <p>{definition.unit === 'km' ? 'Average distance per trip' : 'Distribution of recorded orders'}</p>
        </div>
        <span className="chart-dot" style={{ backgroundColor: definition.color }} aria-hidden="true" />
      </div>
      <div className={`chart-area${definition.type === 'pie' ? ' chart-area-pie' : ''}`}>
        {loading ? (
          <div className="chart-message">Loading chart…</div>
        ) : chartData.length === 0 ? (
          <div className="chart-message">No chart data available.</div>
        ) : definition.type === 'pie' ? (
          <ResponsiveContainer width="100%" height="100%">
            <PieChart>
              <Pie
                data={chartData}
                dataKey="value"
                nameKey="name"
                innerRadius="57%"
                outerRadius="82%"
                paddingAngle={3}
                stroke="none"
              >
                {chartData.map((entry, index) => (
                  <Cell key={entry.name} fill={CHART_COLORS[index % CHART_COLORS.length]} />
                ))}
              </Pie>
              <Tooltip content={<ChartTooltip unit={definition.unit} />} />
            </PieChart>
          </ResponsiveContainer>
        ) : (
          <ResponsiveContainer width="100%" height="100%">
            <BarChart
              data={chartData}
              layout="vertical"
              margin={{ top: 4, right: 16, left: 0, bottom: 4 }}
            >
              <CartesianGrid horizontal={false} stroke="#edf0ec" />
              <XAxis type="number" hide />
              <YAxis
                type="category"
                dataKey="name"
                axisLine={false}
                tickLine={false}
                width={112}
                tick={{ fill: '#747d76', fontSize: 12 }}
              />
              <Tooltip content={<ChartTooltip unit={definition.unit} />} cursor={{ fill: '#f5f7f4' }} />
              <Bar dataKey="value" fill={definition.color} radius={[0, 5, 5, 0]} barSize={17} />
            </BarChart>
          </ResponsiveContainer>
        )}
      </div>
      {definition.type === 'pie' && chartData.length > 0 && !loading && (
        <div className="chart-legend">
          {chartData.map((entry, index) => (
            <span key={entry.name}>
              <i style={{ backgroundColor: CHART_COLORS[index % CHART_COLORS.length] }} />
              {entry.name}
            </span>
          ))}
        </div>
      )}
    </section>
  )
}

function SummaryCard({ label, value, detail, icon }) {
  return (
    <article className="summary-card">
      <div className="summary-topline">
        <span className="summary-label">{label}</span>
        <span className="summary-icon" aria-hidden="true">{icon}</span>
      </div>
      <strong className="summary-value">{value}</strong>
      <span className="summary-detail">{detail}</span>
    </article>
  )
}

function FilterSelect({ label, value, options, optionKey, onChange }) {
  const emptyLabel = {
    City: 'All cities',
    Weather: 'All weather',
    Traffic: 'All traffic',
    Vehicle: 'All vehicles',
    Festival: 'All festivals',
    'Order type': 'All order types',
  }[label]

  return (
    <label className="filter-control">
      <span>{label}</span>
      <select value={value} onChange={(event) => onChange(event.target.value)}>
        <option value="">{emptyLabel}</option>
        {getRows(options).map((option) => {
          const item = option[optionKey]
          if (item == null || String(item).toLowerCase() === 'nan') return null
          return <option key={item} value={item}>{item}</option>
        })}
      </select>
    </label>
  )
}

function OrdersTable({ rows, loading, error }) {
  return (
    <div className="table-scroll">
      <table>
        <thead>
          <tr>
            <th>Order ID</th>
            <th>City</th>
            <th>Delivery person</th>
            <th>Rating</th>
            <th>Weather</th>
            <th>Traffic</th>
            <th>Vehicle</th>
            <th>Order type</th>
            <th>Festival</th>
          </tr>
        </thead>
        <tbody>
          {loading ? (
            <tr><td className="table-state" colSpan="9">Filtering delivery records from JSON…</td></tr>
          ) : error ? (
            <tr><td className="table-state table-error" colSpan="9">{error}</td></tr>
          ) : rows.length === 0 ? (
            <tr><td className="table-state" colSpan="9">No delivery records match these filters.</td></tr>
          ) : rows.map((order, index) => (
            <tr key={`${order.id ?? 'order'}-${index}`}>
              <td className="order-id">{order.id ?? '—'}</td>
              <td>{order.city ?? '—'}</td>
              <td>{order.delivery_person_id ?? '—'}</td>
              <td>{formatNumber(order.delivery_person_ratings, 1)}</td>
              <td>{order.weather ?? '—'}</td>
              <td>{order.traffic_density ?? '—'}</td>
              <td>{order.vehicle_type ?? '—'}</td>
              <td>{order.order_type ?? '—'}</td>
              <td>{order.festival ?? '—'}</td>
            </tr>
          ))}
        </tbody>
      </table>
    </div>
  )
}

function App() {
  const [dashboard, setDashboard] = useState({
    summary: [],
    orders_by_city: [],
    orders_by_traffic: [],
    orders_by_weather: [],
    orders_by_vehicle: [],
    orders_by_festival: [],
    distance_by_city: [],
    filters: null,
  })

  const [cacheStatus, setCacheStatus] = useState(null)
  const [isCacheReady, setIsCacheReady] = useState(false)
  const [loadingInitial, setLoadingInitial] = useState(true)
  const [refreshing, setRefreshing] = useState(false)
  const [backendError, setBackendError] = useState('')
  const [dashboardError, setDashboardError] = useState('')

  const [filters, setFilters] = useState(EMPTY_FILTERS)
  const [orders, setOrders] = useState([])
  const [loadingOrders, setLoadingOrders] = useState(false)
  const [ordersError, setOrdersError] = useState('')
  const [cacheVersion, setCacheVersion] = useState(0)

  // Load complete dashboard data from single cached endpoint
  const loadDashboardData = useCallback(async () => {
    try {
      const data = await fetchJson('/api/dashboard')
      setDashboard(data)
      setDashboardError('')
      return true
    } catch (err) {
      setDashboardError(err.message || 'Failed to load dashboard data.')
      return false
    }
  }, [])

  // Poll cache-status on mount until ready, then fetch /api/dashboard once
  useEffect(() => {
    let timer = null
    let active = true

    async function checkStatus() {
      try {
        const status = await fetchJson('/api/cache-status')
        if (!active) return

        setCacheStatus(status)
        setBackendError('')

        if (status.ready) {
          setIsCacheReady(true)
          await loadDashboardData()
          if (active) setLoadingInitial(false)
        } else if (status.errors?.length) {
          setBackendError(
            `The JSON cache could not be loaded: ${status.errors.join('; ')}. ` +
            'Run backend.py to generate dashboard_cache.json, then retry.'
          )
          setLoadingInitial(false)
        } else {
          timer = setTimeout(checkStatus, 2500)
        }
      } catch {
        if (!active) return
        setBackendError('Backend unavailable. Make sure the FastAPI server is running.')
        timer = setTimeout(checkStatus, 4000)
      }
    }

    checkStatus()

    return () => {
      active = false
      if (timer) clearTimeout(timer)
    }
  }, [loadDashboardData])

  // Reload the JSON written by backend.py; the API does not run Hive.
  const handleRefresh = async () => {
    if (refreshing) return
    setRefreshing(true)
    setDashboardError('')

    try {
      const refreshedData = await fetchJson('/api/refresh', { method: 'POST' })
      setDashboard(refreshedData)
      const status = await fetchJson('/api/cache-status').catch(() => null)
      if (status) setCacheStatus(status)
      setIsCacheReady(true)
      setLoadingInitial(false)
      setBackendError('')
      setCacheVersion((version) => version + 1)
    } catch (err) {
      setDashboardError(`Refresh failed: ${err.message}`)
    } finally {
      setRefreshing(false)
    }
  }

  // Load filtered records table only when cache is ready
  const orderQuery = useMemo(() => {
    const params = new URLSearchParams({ limit: '100' })
    Object.entries(filters).forEach(([key, value]) => {
      if (value) params.set(key, value)
    })
    return params.toString()
  }, [filters])

  useEffect(() => {
    if (!isCacheReady) return

    const controller = new AbortController()
    setLoadingOrders(true)
    setOrdersError('')

    fetchJson(`/api/orders?${orderQuery}`, { signal: controller.signal })
      .then((data) => setOrders(getRows(data)))
      .catch((error) => {
        if (error.name !== 'AbortError') {
          setOrdersError(`Could not load delivery records: ${error.message}`)
        }
      })
      .finally(() => {
        if (!controller.signal.aborted) setLoadingOrders(false)
      })

    return () => controller.abort()
  }, [orderQuery, isCacheReady, cacheVersion])

  const summary = getRows(dashboard.summary)[0] || {}
  const summaryCards = [
    { label: 'Total Orders', value: formatNumber(summary.total_orders), detail: 'Orders in the dataset', icon: '↗' },
    { label: 'Delivery Persons', value: formatNumber(summary.total_delivery_persons), detail: 'Unique delivery partners', icon: '◎' },
    { label: 'Cities', value: formatNumber(summary.total_cities), detail: 'Active delivery cities', icon: '⌖' },
    { label: 'Average Rating', value: formatNumber(summary.average_rating, 2), detail: 'Delivery partner rating', icon: '☆' },
  ]

  function updateFilter(key, value) {
    setFilters((current) => ({ ...current, [key]: value }))
  }

  // Initial loading or backend error overlay
  if (loadingInitial || (backendError && !isCacheReady)) {
    return (
      <main className="dashboard-loading-view">
        <div className="loading-modal">
          {backendError ? (
            <>
              <div className="status-badge error-badge">Connection Error</div>
              <h1>{backendError.includes('JSON cache') ? 'JSON cache unavailable' : 'Backend Unavailable'}</h1>
              <p>{backendError}</p>
              <p className="loading-subtext">{backendError.includes('JSON cache') ? 'Generate the cache with python backend.py, then reload the JSON.' : 'Waiting for the FastAPI server to be reachable…'}</p>
              <button
                className="refresh-button"
                type="button"
                onClick={handleRefresh}
                disabled={refreshing}
              >
                {refreshing ? 'Reloading JSON…' : 'Retry JSON load'}
              </button>
            </>
          ) : (
            <>
              <div className="loading-spinner" />
              <div className="status-badge hive-badge">Loading JSON cache</div>
              <h1>Loading dashboard data…</h1>
              <p>Please wait while the JSON cache is loaded.</p>
              <p className="loading-subtext">
                Run backend.py separately to regenerate dashboard_cache.json from Hive.
              </p>
            </>
          )}
        </div>
      </main>
    )
  }

  return (
    <main className="dashboard">
      <header className="page-header">
        <div className="brand-mark" aria-hidden="true">fd</div>
        <div className="header-copy">
          <div className="eyebrow">OPERATIONS OVERVIEW <span>•</span> FOOD DELIVERY</div>
          <h1>Food Delivery Demand Analytics</h1>
          <p>Food delivery insights served from the generated JSON cache.</p>
        </div>

        <div className="header-actions">
          <button
            className="refresh-button"
            type="button"
            onClick={handleRefresh}
            disabled={refreshing}
          >
            {refreshing ? (
              <>
                <span className="spinner-inline" aria-hidden="true" />
                Reloading JSON…
              </>
            ) : (
              <>
                <span className="refresh-icon" aria-hidden="true">↻</span>
                Reload JSON
              </>
            )}
          </button>
        </div>
      </header>

      {refreshing && (
        <div className="notice refresh-notice" role="status">
          <span className="spinner-inline" /> Reloading dashboard_cache.json…
        </div>
      )}

      {dashboardError && <div className="notice error-notice" role="status">{dashboardError}</div>}
      {!cacheStatus?.orders_ready && (
        <div className="notice error-notice" role="status">
          The cache is missing individual delivery records. Run <code>python backend.py</code>,
          then select “Reload JSON”.
        </div>
      )}

      <section className="summary-grid" aria-label="Delivery summary">
        {summaryCards.map((card) => (
          <SummaryCard
            key={card.label}
            {...card}
            value={card.value}
          />
        ))}
      </section>

      <div className="section-heading">
        <div>
          <span className="eyebrow">DEMAND BREAKDOWN</span>
          <h2>Where and how orders happen</h2>
        </div>
        <span className="section-caption">Loaded from dashboard_cache.json</span>
      </div>

      <section className="charts-grid" aria-label="Order charts">
        {chartDefinitions.map((definition) => (
          <ChartCard
            key={definition.key}
            definition={definition}
            data={dashboard[definition.key]}
            loading={refreshing && !dashboard[definition.key]?.length}
          />
        ))}
      </section>

      <section className="records-section">
        <div className="records-heading">
          <div>
            <span className="eyebrow">DELIVERY DATA</span>
            <h2>Delivery records</h2>
            <p>Filter individual orders loaded from the JSON cache.</p>
          </div>
          <button className="reset-button" type="button" onClick={() => setFilters(EMPTY_FILTERS)}>
            Reset filters
          </button>
        </div>

        <div className="filters-panel" aria-label="Filter delivery records">
          <FilterSelect label="City" value={filters.city} options={dashboard.filters?.cities} optionKey="city" onChange={(value) => updateFilter('city', value)} />
          <FilterSelect label="Weather" value={filters.weather} options={dashboard.filters?.weather} optionKey="weather" onChange={(value) => updateFilter('weather', value)} />
          <FilterSelect label="Traffic" value={filters.traffic} options={dashboard.filters?.traffic} optionKey="traffic_density" onChange={(value) => updateFilter('traffic', value)} />
          <FilterSelect label="Vehicle" value={filters.vehicle} options={dashboard.filters?.vehicles} optionKey="vehicle_type" onChange={(value) => updateFilter('vehicle', value)} />
          <FilterSelect label="Festival" value={filters.festival} options={dashboard.filters?.festivals} optionKey="festival" onChange={(value) => updateFilter('festival', value)} />
          <FilterSelect label="Order type" value={filters.order_type} options={dashboard.filters?.order_types} optionKey="order_type" onChange={(value) => updateFilter('order_type', value)} />
        </div>

        <div className="table-meta">
          <span>{loadingOrders ? 'Filtering cached delivery records…' : `${formatNumber(orders.length)} records shown`}</span>
          <span>Showing up to 100 records</span>
        </div>
        <OrdersTable rows={orders} loading={loadingOrders} error={ordersError} />
      </section>

      <footer className="page-footer">
        <span>Food Delivery Demand Analytics</span>
        <span>Hive JSON export • FastAPI • React + Vite</span>
      </footer>
    </main>
  )
}

export default App
