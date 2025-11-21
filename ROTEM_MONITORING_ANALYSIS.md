# Rotem API Monitoring Analysis & Improvement Recommendations

## Executive Summary

This document analyzes the current Rotem web scraper implementation and available API data to identify opportunities for enhanced monitoring capabilities. Based on the analysis, we can significantly improve real-time monitoring, alerting, and predictive analytics by better utilizing the rich sensor data already available from the Rotem API.

---

## 1. Current Data Collection Analysis

### 1.1 Available API Endpoints

The Rotem scraper currently uses the following endpoints:

#### Primary Endpoint: `RNBL_GetCommandData`
- **Purpose**: Retrieves real-time sensor data for a specific house
- **Method**: POST
- **Returns**: Comprehensive sensor data in structured format
- **Frequency**: Called for each house (1-8) every 5 minutes via Celery tasks

#### Supporting Endpoints:
- `Login` - Authentication and token retrieval
- `GetSiteControllersInfo` - Controller hardware information
- `GetJsGlobals` - System configuration
- `GetFarmRegistration` - Farm metadata

### 1.2 Data Structure from `RNBL_GetCommandData`

The API response contains `reponseObj.dsData` with the following sections:

#### **General Section** (Basic House Parameters)
Currently extracted parameters:
- `Growth_Day` - Current chicken age in days ✅ (used)
- `Average_Temperature` - Average house temperature ✅ (partially used)
- `Set_Temperature` - Target temperature ✅ (partially used)
- `Inside_Humidity` - Humidity percentage ✅ (partially used)
- `Static_Pressure` - Air pressure ✅ (partially used)
- `House_Connection_Status` - Controller connectivity ✅ (partially used)

**Additional Available Parameters** (NOT currently extracted):
- `Outside_Temperature` - External ambient temperature ❌
- `Current_Level_CFM` - Airflow in CFM ❌
- `CFM_Percentage` - Airflow percentage ❌
- `Current_Birds_Count_In_House` - Live bird count ❌
- `Birds_Livability` - Mortality/livability percentage ❌
- `Vent_Level` - Ventilation level percentage ❌
- Set point values for various parameters ❌
- Alarm thresholds (high/low values) ❌

#### **TempSensor Section** (Temperature Sensors Array)
Currently extracted:
- Individual temperature sensors (up to 9 sensors per house) ✅
- Tunnel temperature ✅
- Wind chill temperature ✅

**Additional Available Data**:
- Attic temperature ❌
- Individual sensor status/quality indicators ❌
- Sensor location identifiers ❌
- Historical sensor readings (if available) ❌

#### **Consumption Section** (Resource Usage)
Currently extracted:
- `Daily_Water` - Water consumption ✅
- `Daily_Feed` - Feed consumption ✅

**Additional Available Data**:
- Cumulative consumption values ❌
- Consumption trends ❌
- Per-period consumption (hourly, daily, weekly) ❌
- Consumption efficiency metrics ❌

#### **DigitalOut Section** (System Components Status)
Currently extracted:
- Component status (On/Off) ✅ (partially)

**Available But Underutilized**:
- Fan status (Tunnel_Fans, Exh_Fans, Stir_Fans) - Status only, not runtime/duty cycle ❌
- Heater status - Status only, not energy consumption ❌
- Cooling Pad status - Status only, not efficiency ❌
- Light status - Status only, not dimming level ❌
- Feed system status (Auger, Feeding) - Status only, not feed rate ❌
- Vent positions (Air_Vent, Tunnel_Curtain) - Status only, not percentage open ❌

**Missing Critical Monitoring**:
- Equipment runtime hours (for maintenance scheduling) ❌
- Equipment duty cycle percentages ❌
- Energy consumption per component ❌
- Component health indicators ❌
- Failure alerts from controllers ❌

#### **AnalogOut Section** (Control Settings)
Currently extracted:
- Control setting values ✅ (partially)

**Additional Available Data**:
- Target set points vs actual values ❌
- Control loop status (auto/manual) ❌
- PID controller parameters ❌
- Control system response times ❌

#### **FeedInv Section** (Feed Inventory)
Currently extracted:
- Silo levels ✅ (in views but not in scraper service)

**Additional Available Data**:
- Feed type per silo ❌
- Feed consumption rate per silo ❌
- Low-level alerts ❌
- Refill scheduling ❌
- Feed cost tracking ❌

#### **AvgWeight Section** (Bird Weight Data)
Currently extracted:
- Average weight ✅ (in views but not in scraper service)

**Additional Available Data**:
- Weight distribution statistics ❌
- Growth rate calculations ❌
- Weight trend analysis ❌
- FCR (Feed Conversion Ratio) calculations ❌

#### **Other Available Sections** (NOT Currently Processed)
- `Humidity` array - Detailed humidity data ❌
- `Pressure` array - Detailed pressure readings ❌
- `CO2` array - CO2 levels (air quality) ❌
- `Ammonia` array - Ammonia levels (air quality) ❌
- `Wind` array - Wind speed and direction ❌
- `Ventilation` array - Ventilation metrics ❌
- `Livability` array - Detailed mortality/livability data ❌

---

## 2. Current Monitoring Capabilities

### 2.1 What's Working Well

✅ **Basic Sensor Data Collection**:
- Temperature, humidity, pressure collection
- Growth_Day tracking for age-based task scheduling
- Water and feed consumption tracking
- House-specific data isolation

✅ **ML Analysis Foundation**:
- Anomaly detection framework in place
- Equipment failure prediction models
- Optimization recommendation engine

✅ **Data Infrastructure**:
- Time-series database structure (RotemDataPoint model)
- Controller-based data organization
- Quality flags (good, warning, error, no_data)

### 2.2 Current Limitations

❌ **Incomplete Data Extraction**:
- Many available parameters not being collected
- Missing metadata (alarm thresholds, set points, status flags)
- DigitalOut components tracked by status only, not performance metrics

❌ **Limited Real-time Monitoring**:
- No threshold-based alerts
- No equipment health monitoring
- No trend analysis in real-time
- No comparative analysis across houses

❌ **Insufficient Equipment Tracking**:
- Equipment runtime not tracked
- Maintenance schedules not automated
- Energy consumption not calculated
- Component efficiency not measured

❌ **Missing Operational Metrics**:
- FCR (Feed Conversion Ratio) not calculated
- Growth rate trends not analyzed
- Feed inventory alerts not implemented
- Cost per bird not tracked

---

## 3. Monitoring Enhancement Opportunities

### 3.1 Enhanced Real-Time Monitoring

#### A. Comprehensive Air Quality Monitoring
**Available Data**: CO2, Ammonia levels in API
**Implementation**:
```python
# Extract from dsData['CO2'] and dsData['Ammonia'] arrays
- CO2 levels (PPM) with thresholds: <1000 normal, 1000-3000 warning, >3000 critical
- Ammonia levels (PPM) with thresholds: <25 normal, 25-50 warning, >50 critical
- Air quality index calculation
- Ventilation efficiency based on air quality
```

**Benefits**:
- Early detection of ventilation issues
- Health risk prevention for birds
- Compliance monitoring for regulations
- Automated alerting for poor air quality

#### B. Equipment Performance Monitoring
**Available Data**: DigitalOut status, AnalogOut values, runtime tracking
**Implementation**:
```python
# Track equipment states and calculate:
- Fan runtime hours (for maintenance scheduling)
- Heater efficiency (temperature rise vs energy)
- Cooling pad effectiveness (temperature drop vs activation)
- Feed system reliability (feed rate consistency)
- Equipment duty cycles (on/off frequency)
```

**Benefits**:
- Predictive maintenance scheduling
- Energy consumption optimization
- Equipment failure prediction improvement
- Cost reduction through efficient operation

#### C. Growth & Performance Analytics
**Available Data**: Growth_Day, AvgWeight, Daily_Feed, Daily_Water
**Implementation**:
```python
# Calculate key metrics:
- FCR = Feed Consumed / Weight Gained
- Average Daily Gain (ADG) = Weight Gain / Days
- Water-to-Feed Ratio = Water / Feed
- Growth Rate Trends over time
- Performance comparison across houses
```

**Benefits**:
- Optimize feed efficiency
- Identify underperforming houses
- Benchmark performance
- ROI tracking per house/flock

#### D. Feed Inventory Management
**Available Data**: FeedInv array with silo levels
**Implementation**:
```python
# Extract and monitor:
- Silo levels (current, percentage full)
- Consumption rate per silo
- Days until empty calculation
- Low-level alerts (e.g., <20% capacity)
- Feed type tracking per silo
- Cost per silo/total inventory value
```

**Benefits**:
- Prevent feed runouts
- Optimize ordering schedule
- Reduce waste through better planning
- Cost tracking and optimization

### 3.2 Advanced Alerting System

#### A. Threshold-Based Alerts
**Implementation**:
```python
# Monitor and alert on:
1. Temperature anomalies
   - High: >target + 2°C for >30 minutes
   - Low: <target - 2°C for >30 minutes
   - Rapid changes: >3°C in 10 minutes

2. Air quality alerts
   - CO2 > 3000 PPM (critical)
   - Ammonia > 50 PPM (critical)
   - Poor ventilation detection

3. Equipment alerts
   - Fan failure (expected on but off)
   - Heater failure (temp below target, heater off)
   - Feed system issues (no consumption detected)
   - Sensor failures (stale data >15 minutes)

4. Performance alerts
   - FCR above threshold
   - Growth rate below expected
   - Mortality rate spike
   - Feed inventory low
```

#### B. Predictive Alerts
**Implementation**:
```python
# ML-based predictive alerts:
- Equipment failure prediction (from ML models)
- Performance degradation detection
- Environmental trend analysis
- Maintenance scheduling recommendations
```

### 3.3 Historical Trend Analysis

#### A. Trend Dashboards
**Available Data**: All historical data points stored in RotemDataPoint
**Implementation**:
```python
# Analyze trends for:
- Temperature patterns (daily, weekly cycles)
- Humidity trends and seasonal variations
- Consumption trends (water, feed efficiency)
- Equipment usage patterns
- Performance metrics over time
- Comparative analysis (house vs house, flock vs flock)
```

#### B. Performance Benchmarking
**Implementation**:
```python
# Compare:
- Current flock vs previous flocks
- House performance vs farm average
- Farm performance vs industry standards
- Seasonal performance variations
```

### 3.4 Operational Efficiency Monitoring

#### A. Energy Consumption Tracking
**Available Data**: DigitalOut equipment status, runtime
**Implementation**:
```python
# Calculate:
- Fan energy consumption (based on runtime and rated power)
- Heater energy consumption
- Total house energy usage
- Energy cost per bird
- Energy efficiency trends
```

#### B. Resource Utilization
**Available Data**: Consumption, equipment status
**Implementation**:
```python
# Monitor:
- Water usage efficiency (liters per bird per day)
- Feed conversion efficiency
- Equipment utilization rates
- House capacity utilization
```

---

## 4. Implementation Recommendations

### 4.1 High Priority Enhancements

#### 1. Complete Data Extraction
**Action**: Update `scraper_service.py` to extract ALL available data fields
```python
# Priority fields to add:
1. Outside_Temperature (General)
2. Current_Level_CFM, CFM_Percentage (General)
3. Current_Birds_Count_In_House (General)
4. Birds_Livability (General)
5. CO2 array (air quality)
6. Ammonia array (air quality)
7. Wind array (wind speed/direction)
8. Complete DigitalOut processing (with runtime tracking)
9. FeedInv array (silo levels)
10. AvgWeight array (with historical tracking)
```

#### 2. Enhanced Data Model
**Action**: Expand `RotemDataPoint` model to capture more metadata
```python
# Add fields:
- alarm_threshold_high
- alarm_threshold_low
- set_point_value
- equipment_runtime_hours
- equipment_duty_cycle
- sensor_quality_indicator
```

#### 3. Real-Time Alert System
**Action**: Implement threshold-based alerting
```python
# Create new model: RotemAlert
- alert_type (temperature, air_quality, equipment, performance)
- severity (info, warning, critical)
- threshold_values
- notification_channels
- alert_history
```

#### 4. Equipment Monitoring Service
**Action**: Create dedicated service for equipment tracking
```python
# New service: EquipmentMonitoringService
- Track runtime hours for each component
- Calculate duty cycles
- Schedule maintenance alerts
- Monitor equipment health
- Energy consumption calculations
```

### 4.2 Medium Priority Enhancements

#### 1. Performance Metrics Calculator
**Action**: Create service to calculate operational metrics
```python
# New service: PerformanceMetricsService
- Calculate FCR (Feed Conversion Ratio)
- Calculate ADG (Average Daily Gain)
- Calculate water-to-feed ratio
- Track growth rate trends
- Performance benchmarking
```

#### 2. Feed Inventory Management
**Action**: Implement feed inventory tracking and alerts
```python
# Enhance FeedInv processing:
- Track silo levels with timestamps
- Calculate consumption rates
- Predict days until empty
- Low-level alerts (<20%, <10%)
- Reorder recommendations
```

#### 3. Historical Trend Analysis
**Action**: Build trend analysis endpoints and dashboards
```python
# New endpoints:
- /api/rotem/trends/temperature/
- /api/rotem/trends/consumption/
- /api/rotem/trends/performance/
- /api/rotem/trends/equipment/
- /api/rotem/benchmarks/
```

### 4.3 Low Priority (Nice to Have)

#### 1. Comparative Analytics
- House-to-house comparisons
- Flock-to-flock comparisons
- Farm-to-industry benchmarks

#### 2. Cost Tracking
- Energy costs per house
- Feed costs per bird
- Total operational costs
- ROI calculations

#### 3. Advanced Visualization
- Heat maps for sensor distribution
- Real-time equipment status maps
- 3D visualization of house conditions
- Interactive trend charts

---

## 5. Specific Code Improvements

### 5.1 Enhanced Scraper Service

#### Current Implementation Issues:
```python
# In scraper_service.py _process_data_points():
- Only processes General, TempSensor, Consumption, DigitalOut
- Missing: CO2, Ammonia, Wind, Ventilation, Livability, FeedInv, AvgWeight
- DigitalOut only tracks status, not runtime/performance
- No alarm threshold extraction
- No set point tracking
```

#### Recommended Enhancements:
```python
# Add processing for all data sections:
1. Complete General array processing (extract all parameters)
2. Process CO2 array for air quality
3. Process Ammonia array for air quality  
4. Process Wind array for ventilation efficiency
5. Process FeedInv array for inventory management
6. Process AvgWeight array for performance tracking
7. Enhanced DigitalOut processing (track state changes for runtime)
8. Extract alarm thresholds and set points from all sections
9. Store equipment state changes with timestamps
10. Calculate derived metrics (FCR, growth rates, etc.)
```

### 5.2 New Models Needed

#### RotemAlert Model
```python
class RotemAlert(models.Model):
    farm = ForeignKey(Farm)
    controller = ForeignKey(RotemController)
    house_number = IntegerField()
    alert_type = CharField()  # temperature, air_quality, equipment, etc.
    severity = CharField()  # info, warning, critical
    parameter_name = CharField()
    current_value = FloatField()
    threshold_value = FloatField()
    message = TextField()
    is_acknowledged = BooleanField()
    acknowledged_by = ForeignKey(User)
    acknowledged_at = DateTimeField()
    created_at = DateTimeField()
```

#### EquipmentRuntime Model
```python
class EquipmentRuntime(models.Model):
    controller = ForeignKey(RotemController)
    house_number = IntegerField()
    equipment_name = CharField()  # Fan_1, Heater_1, etc.
    status = CharField()  # On, Off
    last_state_change = DateTimeField()
    total_runtime_hours = FloatField()
    current_session_start = DateTimeField()
    maintenance_due_hours = FloatField()
    last_maintenance = DateTimeField()
```

### 5.3 New Services

#### AlertService
```python
class RotemAlertService:
    - check_thresholds(data_point)
    - create_alert(alert_type, severity, message)
    - send_notifications(alert)
    - acknowledge_alert(alert_id, user)
    - get_active_alerts(house_number)
    - get_alert_history(house_number, days)
```

#### EquipmentMonitoringService
```python
class EquipmentMonitoringService:
    - track_equipment_state(controller, house, equipment, state)
    - calculate_runtime_hours(equipment)
    - get_maintenance_schedule(equipment)
    - calculate_duty_cycle(equipment, period)
    - estimate_energy_consumption(equipment, runtime)
```

#### PerformanceMetricsService
```python
class PerformanceMetricsService:
    - calculate_fcr(house, start_date, end_date)
    - calculate_adg(house, start_date, end_date)
    - calculate_water_to_feed_ratio(house, period)
    - track_growth_rate(house, days)
    - benchmark_house_performance(house, comparison_group)
```

---

## 6. API Response Data Mapping

### Complete Data Field Inventory

Based on the `RNBL_GetCommandData` endpoint, here's the complete mapping of available data:

#### General Array Parameters:
| Parameter Name | Data Type | Unit | Current Status | Monitoring Value |
|---------------|-----------|------|----------------|------------------|
| Growth_Day | Integer | days | ✅ Extracted | High - Age tracking |
| Average_Temperature | Float | °C | ✅ Extracted | High - Core metric |
| Outside_Temperature | Float | °C | ❌ Missing | High - Ventilation efficiency |
| Set_Temperature | Float | °C | ✅ Partial | High - Control efficiency |
| Inside_Humidity | Float | % | ✅ Extracted | High - Health metric |
| Static_Pressure | Float | BAR | ✅ Extracted | Medium - Ventilation |
| Current_Level_CFM | Float | CFM | ❌ Missing | High - Airflow monitoring |
| CFM_Percentage | Float | % | ❌ Missing | Medium - Airflow efficiency |
| Current_Birds_Count_In_House | Integer | count | ❌ Missing | High - Capacity tracking |
| Birds_Livability | Float | % | ❌ Missing | High - Performance metric |
| Vent_Level | Float | % | ❌ Missing | Medium - Ventilation control |
| House_Connection_Status | Integer | status | ✅ Partial | High - Connectivity |
| Alarm thresholds (high/low) | Float | various | ❌ Missing | High - Alerting |

#### Consumption Array Parameters:
| Parameter Name | Data Type | Unit | Current Status | Monitoring Value |
|---------------|-----------|------|----------------|------------------|
| Daily_Water | Float | L | ✅ Extracted | High - Resource tracking |
| Daily_Feed | Float | LB | ✅ Extracted | High - Resource tracking |
| Cumulative values | Float | various | ❌ Missing | Medium - Historical tracking |

#### TempSensor Array:
| Sensor Type | Count | Current Status | Monitoring Value |
|------------|-------|----------------|------------------|
| Temperature sensors | Up to 9 | ✅ Extracted | High - Distribution analysis |
| Tunnel temperature | 1 | ✅ Extracted | High - Ventilation |
| Wind chill | 1 | ✅ Extracted | Medium - Environmental |
| Attic temperature | 1 | ❌ Missing | Medium - Insulation check |

#### DigitalOut Array (System Components):
| Component | Current Tracking | Missing Data | Monitoring Value |
|-----------|------------------|--------------|------------------|
| Tunnel_Fans | Status only | Runtime, duty cycle | High - Maintenance |
| Exh_Fans | Status only | Runtime, duty cycle | High - Maintenance |
| Stir_Fans | Status only | Runtime, duty cycle | High - Maintenance |
| Heaters | Status only | Runtime, efficiency | High - Energy tracking |
| Cooling_Pad | Status only | Runtime, effectiveness | High - Efficiency |
| Lights | Status only | Dimming level | Medium - Automation |
| Feed_System | Status only | Feed rate | High - Performance |
| Vents | Status only | Position percentage | Medium - Control |

#### Additional Arrays (Not Currently Processed):
| Array Name | Parameters | Monitoring Value | Priority |
|-----------|------------|------------------|----------|
| CO2 | CO2 levels | High - Air quality | High |
| Ammonia | Ammonia levels | High - Health/safety | High |
| Wind | Speed, direction | Medium - Ventilation | Medium |
| Ventilation | CFM, efficiency | High - Performance | High |
| Livability | Mortality, livability % | High - Performance | High |
| FeedInv | Silo levels | High - Inventory | High |
| AvgWeight | Average weight | High - Performance | High |
| Humidity | Detailed humidity data | Medium - Redundancy | Low |
| Pressure | Detailed pressure data | Medium - Redundancy | Low |

---

## 7. Recommended Implementation Priority

### Phase 1: Critical Data Extraction (Week 1-2)
1. ✅ Extract CO2 and Ammonia arrays (air quality monitoring)
2. ✅ Extract FeedInv array (inventory management)
3. ✅ Extract AvgWeight array (performance tracking)
4. ✅ Extract missing General parameters (outside temp, bird count, etc.)
5. ✅ Extract Wind and Ventilation arrays
6. ✅ Extract alarm thresholds and set points

### Phase 2: Equipment Monitoring (Week 3-4)
1. ✅ Create EquipmentRuntime model
2. ✅ Track equipment state changes with timestamps
3. ✅ Calculate runtime hours for maintenance
4. ✅ Implement duty cycle calculations
5. ✅ Create equipment health dashboard

### Phase 3: Alerting System (Week 5-6)
1. ✅ Create RotemAlert model
2. ✅ Implement threshold-based alert checking
3. ✅ Create alert notification system
4. ✅ Build alert dashboard
5. ✅ Implement alert acknowledgment workflow

### Phase 4: Performance Metrics (Week 7-8)
1. ✅ Create PerformanceMetricsService
2. ✅ Implement FCR calculations
3. ✅ Implement ADG calculations
4. ✅ Create performance dashboard
5. ✅ Implement benchmarking features

### Phase 5: Advanced Analytics (Week 9-10)
1. ✅ Build trend analysis endpoints
2. ✅ Create comparative analytics
3. ✅ Implement energy consumption tracking
4. ✅ Build predictive maintenance system
5. ✅ Create comprehensive reporting

---

## 8. Expected Benefits

### Operational Benefits:
- **Proactive Issue Detection**: Early warning system prevents problems
- **Reduced Mortality**: Better air quality and environmental monitoring
- **Improved Efficiency**: Performance metrics enable optimization
- **Cost Savings**: Energy and feed optimization, predictive maintenance
- **Better Decision Making**: Comprehensive data and analytics

### Technical Benefits:
- **Complete Data Utilization**: Use all available API data
- **Better ML Models**: More data = better predictions
- **Scalable Architecture**: Foundation for future enhancements
- **Industry Standards**: Align with best practices in farm management

---

## 9. Risk Mitigation

### Potential Challenges:
1. **API Rate Limiting**: Monitor request frequency, implement backoff
2. **Data Volume**: Optimize storage, implement data archival
3. **Performance Impact**: Use Celery for async processing, optimize queries
4. **Alert Fatigue**: Implement intelligent alert aggregation
5. **Data Quality**: Implement validation and quality checks

### Mitigation Strategies:
- Implement request queuing and rate limiting
- Use database indexing and query optimization
- Create alert aggregation rules
- Implement data quality validation
- Use caching for frequently accessed data

---

## 10. Next Steps

1. **Review and Approve**: Review this analysis with stakeholders
2. **Prioritize Features**: Select which enhancements to implement first
3. **Create Detailed Specs**: Write detailed technical specifications
4. **Implement Phase 1**: Start with critical data extraction
5. **Test and Iterate**: Test enhancements and iterate based on feedback
6. **Monitor Performance**: Track the impact of new monitoring capabilities

---

## Conclusion

The Rotem API provides rich sensor data that is currently underutilized. By implementing the recommended enhancements, we can transform the system from basic data collection to comprehensive real-time monitoring with predictive capabilities. The improvements will provide significant operational value through better decision-making, proactive issue detection, and performance optimization.

**Key Takeaways**:
- Currently using ~40% of available API data
- Opportunity to add air quality, equipment, and performance monitoring
- Foundation is solid, needs enhancement in data extraction and processing
- ROI is high - better monitoring leads to better farm management and profitability


