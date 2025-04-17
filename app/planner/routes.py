from flask import render_template, redirect, url_for, flash, request, jsonify, session
from flask_login import login_required, current_user
from . import planner_bp
from ..models import BillableHourGoal, Holiday, VacationDay, DailyLog
from .. import db
import datetime

# US federal holidays for demo
US_FEDERAL_HOLIDAYS = [
    ("2025-01-01", "New Year's Day"),
    ("2025-01-20", "Martin Luther King Jr. Day"),
    ("2025-02-17", "Presidents' Day"),
    ("2025-05-26", "Memorial Day"),
    ("2025-07-04", "Independence Day"),
    ("2025-09-01", "Labor Day"),
    ("2025-10-13", "Columbus Day"),
    ("2025-11-11", "Veterans Day"),
    ("2025-11-27", "Thanksgiving Day"),
    ("2025-12-25", "Christmas Day"),
]

MONTHS = [
    "January", "February", "March", "April", "May", "June",
    "July", "August", "September", "October", "November", "December"
]

def get_working_days(year, holidays, vacation_days):
    # Returns a set of all working dates (YYYY-MM-DD) for the year, excluding weekends, holidays, and vacation
    start = datetime.date(year, 1, 1)
    end = datetime.date(year, 12, 31)
    day_count = (end - start).days + 1
    holidays_set = set(h.date for h in holidays)
    vacation_set = set(v.date for v in vacation_days)
    working_days = []
    for n in range(day_count):
        d = start + datetime.timedelta(days=n)
        if d.weekday() >= 5:  # 5=Saturday, 6=Sunday
            continue
        if d in holidays_set or d in vacation_set:
            continue
        working_days.append(d)
    return working_days

def generate_plan(goal, holidays, vacation_days, workload_weights):
    year = goal.year
    annual_goal = goal.annual_goal
    working_days = get_working_days(year, holidays, vacation_days)
    # Count working days per month
    month_working_days = {m: [] for m in MONTHS}
    for d in working_days:
        month_name = MONTHS[d.month - 1]
        month_working_days[month_name].append(d)
    # Calculate weighted total
    total_weighted_days = 0
    weighted_days_per_month = {}
    for m in MONTHS:
        weight = workload_weights.get(m, 1.0)
        count = len(month_working_days[m])
        weighted_days_per_month[m] = count * weight
        total_weighted_days += count * weight
    # Distribute hours per month
    plan = {}
    monthly_targets = {}
    for m in MONTHS:
        if weighted_days_per_month[m] == 0:
            monthly_targets[m] = 0
            continue
        month_goal = (weighted_days_per_month[m] / total_weighted_days) * annual_goal
        daily_target = month_goal / len(month_working_days[m]) if month_working_days[m] else 0
        # Cap daily target to 10 hours, smooth if needed
        if daily_target > 10:
            daily_target = 10
        for d in month_working_days[m]:
            plan[d] = round(daily_target, 2)
        monthly_targets[m] = round(month_goal, 1)
    return plan, monthly_targets

@planner_bp.route('/api/dashboard', methods=['GET'])
@login_required
def dashboard_api():
    user = current_user
    import dateutil.parser
    try:
        month = int(request.args.get('month', datetime.date.today().month))
        year = int(request.args.get('year', datetime.date.today().year))
    except Exception:
        month = datetime.date.today().month
        year = datetime.date.today().year

    goal = BillableHourGoal.query.filter_by(user_id=user.id, year=year).first()
    holidays = Holiday.query.filter_by(user_id=user.id).all()
    vacation_days = VacationDay.query.filter_by(user_id=user.id).all()
    if not goal:
        return jsonify({"error": "Setup incomplete"}), 400
    plan, monthly_targets = generate_plan(goal, holidays, vacation_days, goal.workload_weights)
    today = datetime.date.today()
    daily_plan = {d: h for d, h in plan.items() if d.month == month and d.year == year}
    # Progress tracking
    logs = DailyLog.query.filter(
        DailyLog.user_id==user.id,
        DailyLog.date>=datetime.date(year, 1, 1),
        DailyLog.date<=datetime.date(year, 12, 31)
    ).all()
    logs_by_date = {log.date: log.hours for log in logs}
    month_dates = [d for d in daily_plan.keys()]
    month_actual = sum(logs_by_date.get(d, 0) for d in month_dates)
    month_target = sum(daily_plan.values())
    year_dates = list(plan.keys())
    year_actual = sum(logs_by_date.get(d, 0) for d in year_dates)
    year_target = sum(plan.values())
    # Summary cards
    year_progress = round((year_actual / year_target) * 100, 1) if year_target else 0
    month_progress = round((month_actual / month_target) * 100, 1) if month_target else 0
    # Recent activity (last 4 days)
    recent_days = []
    for i in range(3, -1, -1):
        d = today - datetime.timedelta(days=i)
        target = daily_plan.get(d, 0)
        logged = logs_by_date.get(d, 0)
        if d == today:
            status = 'in-progress' if logged < target else 'success'
            date_str = f"Today, {d.strftime('%b %d')}"
        else:
            status = 'success' if logged >= target else 'warning'
            date_str = d.strftime('%A, %b %d')
        recent_days.append({
            'date': date_str,
            'target': target,
            'logged': logged,
            'status': status
        })
    # Compose response
    return jsonify({
        'yearProgress': year_progress,
        'monthProgress': month_progress,
        'recentDays': recent_days,
        'annualGoal': goal.annual_goal,
        'monthActual': month_actual,
        'monthTarget': month_target,
        'yearActual': year_actual,
        'yearTarget': year_target,
        # Add more fields as needed for summary cards/charts
    })

@planner_bp.route('/', methods=['GET', 'POST'])
@login_required
def dashboard():
    user = current_user
    # Support month/year navigation and custom date range
    import dateutil.parser
    try:
        month = int(request.args.get('month', datetime.date.today().month))
        year = int(request.args.get('year', datetime.date.today().year))
    except Exception:
        month = datetime.date.today().month
        year = datetime.date.today().year

    # Date range controls
    start_date_str = request.args.get('start_date')
    end_date_str = request.args.get('end_date')
    compare_start_str = request.args.get('compare_start')
    compare_end_str = request.args.get('compare_end')
    try:
        start_date = dateutil.parser.parse(start_date_str).date() if start_date_str else None
        end_date = dateutil.parser.parse(end_date_str).date() if end_date_str else None
        compare_start = dateutil.parser.parse(compare_start_str).date() if compare_start_str else None
        compare_end = dateutil.parser.parse(compare_end_str).date() if compare_end_str else None
    except Exception:
        start_date = end_date = compare_start = compare_end = None

    goal = BillableHourGoal.query.filter_by(user_id=user.id, year=year).first()
    holidays = Holiday.query.filter_by(user_id=user.id).all()
    vacation_days = VacationDay.query.filter_by(user_id=user.id).all()
    if not goal:
        flash('Please complete your setup wizard first.', 'warning')
        return redirect(url_for('planner.setup_wizard'))
    plan, monthly_targets = generate_plan(goal, holidays, vacation_days, goal.workload_weights)
    today = datetime.date.today()
    # Show daily plan for selected month
    daily_plan = {d: h for d, h in plan.items() if d.month == month and d.year == year}
    this_month = MONTHS[month - 1]

    # Handle logging hours (for any date)
    if request.method == 'POST':
        log_date = request.form.get('log_date')
        log_hours = request.form.get('log_hours')
        # For modal, redirect back to the same month/year
        redirect_month = request.form.get('redirect_month', month)
        redirect_year = request.form.get('redirect_year', year)
        try:
            log_date_obj = datetime.datetime.strptime(log_date, '%Y-%m-%d').date()
            log_hours_float = float(log_hours)
            # Update or create log
            log = DailyLog.query.filter_by(user_id=user.id, date=log_date_obj).first()
            if log:
                log.hours = log_hours_float
            else:
                log = DailyLog(user_id=user.id, date=log_date_obj, hours=log_hours_float)
                db.session.add(log)
            db.session.commit()
            flash(f'Logged {log_hours_float} hours for {log_date}', 'success')
        except Exception:
            flash('Invalid log entry.', 'danger')
        return redirect(url_for('planner.dashboard', month=redirect_month, year=redirect_year))

    # Progress tracking
    # Get all logs for this user/year
    logs = DailyLog.query.filter(
        DailyLog.user_id==user.id,
        DailyLog.date>=datetime.date(year, 1, 1),
        DailyLog.date<=datetime.date(year, 12, 31)
    ).all()
    logs_by_date = {log.date: log.hours for log in logs}
    # Calculate progress for current month and year
    month_dates = [d for d in daily_plan.keys()]
    month_actual = sum(logs_by_date.get(d, 0) for d in month_dates)
    month_target = sum(daily_plan.values())
    year_dates = list(plan.keys())
    year_actual = sum(logs_by_date.get(d, 0) for d in year_dates)
    year_target = sum(plan.values())
    # Pace/catch-up logic
    days_left = len([d for d in year_dates if d >= today])
    hours_left = max(goal.annual_goal - year_actual, 0)
    catchup_per_day = round(hours_left / days_left, 2) if days_left > 0 else 0
    pace_status = 'on track'
    if year_actual > year_target * (today.timetuple().tm_yday / 365):
        pace_status = f'{round(year_actual - year_target * (today.timetuple().tm_yday / 365), 1)} hours ahead'
    elif year_actual < year_target * (today.timetuple().tm_yday / 365):
        pace_status = f'{round(year_target * (today.timetuple().tm_yday / 365) - year_actual, 1)} hours behind'

    # Calendar structure for current month
    from calendar import monthrange
    first_day = datetime.date(year, month, 1)
    last_day = datetime.date(year, month, monthrange(year, month)[1])
    calendar_days = []
    for n in range((last_day - first_day).days + 1):
        d = first_day + datetime.timedelta(days=n)
        target = daily_plan.get(d)
        logged = logs_by_date.get(d)
        # Determine status
        if target is None:
            status = 'nonwork'  # Not a working day
        elif d == today:
            status = 'today'
        elif logged is None:
            status = 'no-log'
        elif logged >= target:
            status = 'on-track'
        elif 0 < logged < target:
            status = 'partial'
        else:
            status = 'no-log'
        calendar_days.append({
            'date': d,
            'target': target,
            'logged': logged,
            'status': status
        })

    # --- ANALYTICS ---
    # Daily logs for current month (for bar chart)
    month_days = [(first_day + datetime.timedelta(days=n)) for n in range((last_day - first_day).days + 1)]
    month_logs = [logs_by_date.get(d, 0) for d in month_days]
    month_targets = [daily_plan.get(d, 0) for d in month_days]

    # Cumulative actual vs. target for month
    month_cum_actual = []
    month_cum_target = []
    cum_a = 0
    cum_t = 0
    for a, t in zip(month_logs, month_targets):
        cum_a += a
        cum_t += t
        month_cum_actual.append(cum_a)
        month_cum_target.append(cum_t)

    # Cumulative actual vs. target for year
    year_days = sorted([d for d in plan.keys() if d.year == year])
    year_logs = [logs_by_date.get(d, 0) for d in year_days]
    year_targets = [plan.get(d, 0) for d in year_days]
    year_cum_actual = []
    year_cum_target = []
    cum_a = 0
    cum_t = 0
    for a, t in zip(year_logs, year_targets):
        cum_a += a
        cum_t += t
        year_cum_actual.append(cum_a)
        year_cum_target.append(cum_t)

    # Weekday distribution (for pie/bar)
    from collections import Counter
    weekday_hours = Counter()
    for d, h in logs_by_date.items():
        weekday_hours[d.strftime('%A')] += h
    weekday_labels = ['Monday','Tuesday','Wednesday','Thursday','Friday','Saturday','Sunday']
    weekday_data = [weekday_hours.get(day, 0) for day in weekday_labels]
    # Most productive weekday
    if weekday_hours:
        most_productive_day = max(weekday_hours, key=weekday_hours.get)
    else:
        most_productive_day = None

    # Streaks (consecutive days with hours logged)
    streak = 0
    max_streak = 0
    for d in sorted(year_days):
        if logs_by_date.get(d, 0) > 0:
            streak += 1
            max_streak = max(max_streak, streak)
        else:
            streak = 0
    # Rolling 7-day average (for trend)
    import numpy as np
    def rolling_average(data, window):
        arr = np.array(data)
        if len(arr) < window:
            return [float(np.mean(arr))]*len(arr) if len(arr)>0 else [0]
        return np.convolve(arr, np.ones(window)/window, mode='valid').tolist()
    rolling_7d = rolling_average(year_logs, 7)

    # --- Comparison analytics ---
    cmp_month_days = []
    cmp_month_logs = []
    cmp_month_targets = []
    cmp_month_cum_actual = []
    cmp_month_cum_target = []
    if compare_start and compare_end:
        cmp_dates = [compare_start + datetime.timedelta(days=i) for i in range((compare_end - compare_start).days + 1)]
        cmp_logs = {log.date: log.hours for log in DailyLog.query.filter(DailyLog.user_id==user.id, DailyLog.date >= compare_start, DailyLog.date <= compare_end).all()}
        cmp_targets = {d: plan.get(d, 0) for d in cmp_dates}
        cmp_month_days = cmp_dates
        cmp_month_logs = [cmp_logs.get(d, 0) for d in cmp_dates]
        cmp_month_targets = [cmp_targets.get(d, 0) for d in cmp_dates]
        # Cumulative
        cum_actual = 0
        cum_target = 0
        for a, t in zip(cmp_month_logs, cmp_month_targets):
            cum_actual += a
            cum_target += t
            cmp_month_cum_actual.append(cum_actual)
            cmp_month_cum_target.append(cum_target)

    # --- Key Statistics ---
    def avg_billable(logs, days):
        if not days:
            return 0
        workdays = [d for d in days if d.weekday() < 5]  # Mon-Fri
        if not workdays:
            return 0
        total = sum([logs.get(d, 0) for d in workdays])
        return total / len(workdays)

    # Helper for percent change
    def percent_change(new, old):
        if old == 0:
            return None if new == 0 else 100.0
        return ((new - old) / old) * 100

    # Collect logs for all periods
    all_logs = {log.date: log.hours for log in DailyLog.query.filter(DailyLog.user_id==user.id).all()}
    today_dt = today

    # Primary period
    primary_days = month_days if start_date and end_date else month_days
    primary_avg = avg_billable({d: l for d, l in zip(month_days, month_logs)}, month_days)
    # Comparison period
    cmp_avg = avg_billable({d: l for d, l in zip(cmp_month_days, cmp_month_logs)}, cmp_month_days) if cmp_month_days else None

    # --- Stringify date lists for template ---
    month_days_str = [d.strftime('%Y-%m-%d') for d in month_days]
    year_days_str = [d.strftime('%Y-%m-%d') for d in year_days]
    cmp_month_days_str = [d.strftime('%Y-%m-%d') for d in cmp_month_days] if cmp_month_days else []

    # Last 14 and 30 days
    last14 = [today_dt - datetime.timedelta(days=i) for i in range(14)][::-1]
    last30 = [today_dt - datetime.timedelta(days=i) for i in range(30)][::-1]
    avg_14 = avg_billable(all_logs, last14)
    avg_30 = avg_billable(all_logs, last30)

    # Year-to-date (from Jan 1 to today)
    ytd_days = [datetime.date(today_dt.year, 1, 1) + datetime.timedelta(days=i) for i in range((today_dt - datetime.date(today_dt.year, 1, 1)).days + 1)]
    avg_ytd = avg_billable(all_logs, ytd_days)

    # Percent changes
    stat_pct_cmp = percent_change(primary_avg, cmp_avg) if cmp_avg is not None else None
    stat_pct_14_30 = percent_change(avg_14, avg_30) if avg_30 else None
    stat_pct_14_ytd = percent_change(avg_14, avg_ytd) if avg_ytd else None
    stat_pct_30_ytd = percent_change(avg_30, avg_ytd) if avg_ytd else None

    # --- Goal Progress & Projections ---
    # Total goal (annual)
    annual_goal = goal.annual_goal if goal else 0
    # Actual so far (YTD)
    actual_ytd = sum([all_logs.get(d, 0) for d in ytd_days])
    # Percent complete
    pct_complete = (actual_ytd / annual_goal * 100) if annual_goal else 0
    # Days left in year (workdays only)
    from calendar import monthrange
    last_day = datetime.date(today_dt.year, 12, 31)
    remaining_days = [d for d in [today_dt + datetime.timedelta(days=i) for i in range((last_day - today_dt).days + 1)] if d.weekday() < 5]
    # Required avg per workday to hit goal
    hours_left = max(annual_goal - actual_ytd, 0)
    req_avg = (hours_left / len(remaining_days)) if remaining_days else 0
    # Projected year-end total (based on avg_ytd)
    total_workdays = [d for d in [datetime.date(today_dt.year, 1, 1) + datetime.timedelta(days=i) for i in range((last_day - datetime.date(today_dt.year, 1, 1)).days + 1)] if d.weekday() < 5]
    projected_total = (avg_ytd * len(total_workdays)) if avg_ytd else actual_ytd
    # Days ahead/behind target
    # Compute expected hours as of today (target pace)
    expected_as_of_today = sum([plan.get(d, 0) for d in ytd_days])
    hour_diff = actual_ytd - expected_as_of_today
    avg_day_target = (annual_goal / len(total_workdays)) if total_workdays else 0
    days_ahead_behind = (hour_diff / avg_day_target) if avg_day_target else 0

    # Pass all analytics data to template
    return render_template(
        'planner/dashboard.html',
        monthly_targets=monthly_targets,
        daily_plan=daily_plan,
        this_month=this_month,
        first_day=first_day,
        calendar_days=calendar_days,
        today=today,
        logs_by_date=logs_by_date,
        month_actual=month_actual,
        month_target=month_target,
        year_actual=year_actual,
        year_target=year_target,
        pace_status=pace_status,
        catchup_per_day=catchup_per_day,
        month_days=month_days,
        month_days_str=month_days_str,
        month_logs=month_logs,
        month_targets=month_targets,
        month_cum_actual=month_cum_actual,
        month_cum_target=month_cum_target,
        year_days=year_days,
        year_days_str=year_days_str,
        year_logs=year_logs,
        year_targets=year_targets,
        year_cum_actual=year_cum_actual,
        year_cum_target=year_cum_target,
        weekday_labels=weekday_labels,
        weekday_data=weekday_data,
        most_productive_day=most_productive_day,
        streak=max_streak,
        rolling_7d=rolling_7d,
        cmp_month_days=cmp_month_days,
        cmp_month_days_str=cmp_month_days_str,
        cmp_month_logs=cmp_month_logs,
        cmp_month_targets=cmp_month_targets,
        cmp_month_cum_actual=cmp_month_cum_actual,
        cmp_month_cum_target=cmp_month_cum_target,
        # Stats
        primary_avg=primary_avg,
        cmp_avg=cmp_avg,
        avg_14=avg_14,
        avg_30=avg_30,
        avg_ytd=avg_ytd,
        stat_pct_cmp=stat_pct_cmp,
        stat_pct_14_30=stat_pct_14_30,
        stat_pct_14_ytd=stat_pct_14_ytd,
        stat_pct_30_ytd=stat_pct_30_ytd,
        # Goal progress/projection
        annual_goal=annual_goal,
        actual_ytd=actual_ytd,
        pct_complete=pct_complete,
        req_avg=req_avg,
        projected_total=projected_total,
        days_ahead_behind=days_ahead_behind
    )

import calendar
from flask import jsonify, request

def suggest_catchup_plans(hours_needed, max_workday_hours, weekend_policy):
    """
    Suggest 3 plans (gentle, moderate, aggressive) to catch up or get ahead.
    weekend_policy: dict with keys 'allow', 'max_hours' (e.g., {'allow': True, 'max_hours': 4})
    Returns: list of dicts {label, plan: [{date, hours}], duration, end_date, weekend_days, workdays}
    """
    today = datetime.date.today()
    # Get all remaining days in year
    last_day = datetime.date(today.year, 12, 31)
    days = [today + datetime.timedelta(days=i) for i in range((last_day - today).days + 1)]
    workdays = [d for d in days if d.weekday() < 5]
    weekends = [d for d in days if d.weekday() >= 5]
    plan_options = []

    # Helper to build plan
    def build_plan(num_days, use_weekends):
        plan = []
        hours_left = hours_needed
        d_idx = 0
        while hours_left > 0 and d_idx < len(days):
            d = days[d_idx]
            if d.weekday() < 5:
                assign = min(hours_left, max_workday_hours)
            elif use_weekends and weekend_policy['allow']:
                assign = min(hours_left, weekend_policy['max_hours'])
            else:
                d_idx += 1
                continue
            plan.append({'date': d, 'hours': assign})
            hours_left -= assign
            d_idx += 1
        return plan

    # Gentle: spread over max possible days (use weekends if allowed)
    gentle_plan = build_plan(len(days), use_weekends=True)
    # Moderate: spread over about half as many days (double per-day target)
    moderate_days = max(1, len(days)//2)
    moderate_plan = build_plan(moderate_days, use_weekends=True)
    # Aggressive: as fast as possible (max hours every day until done)
    aggressive_plan = build_plan(999, use_weekends=True)

    for label, plan in zip(['Gentle', 'Moderate', 'Aggressive'], [gentle_plan, moderate_plan, aggressive_plan]):
        if not plan: continue
        duration = (plan[-1]['date'] - plan[0]['date']).days + 1
        end_date = plan[-1]['date']
        weekend_days = sum(1 for x in plan if x['date'].weekday() >= 5)
        workdays = sum(1 for x in plan if x['date'].weekday() < 5)
        plan_options.append({
            'label': label,
            'plan': [{'date': x['date'].isoformat(), 'hours': x['hours']} for x in plan],
            'duration': duration,
            'end_date': end_date.isoformat(),
            'weekend_days': weekend_days,
            'workdays': workdays,
            'total_hours': sum(x['hours'] for x in plan)
        })
    return plan_options

@planner_bp.route('/catchup_plans', methods=['POST'])
def catchup_plans():
    data = request.json
    hours_needed = float(data.get('hours_needed', 0))
    max_workday_hours = float(data.get('max_workday_hours', 8))
    weekend_policy = data.get('weekend_policy', {'allow': False, 'max_hours': 0})
    plans = suggest_catchup_plans(hours_needed, max_workday_hours, weekend_policy)
    return jsonify({'plans': plans})

@planner_bp.route('/setup', methods=['GET', 'POST'])
@login_required
def setup_wizard():
    user = current_user
    year = datetime.date.today().year
    
    # Load or initialize goal
    goal = BillableHourGoal.query.filter_by(user_id=user.id, year=year).first()
    if not goal:
        # Default: 1800 hours, all months normal
        default_weights = {m: 1.0 for m in MONTHS}
        goal = BillableHourGoal(year=year, annual_goal=1800, workload_weights=default_weights, user_id=user.id)
        db.session.add(goal)
        db.session.commit()
    
    # Load holidays
    holidays = Holiday.query.filter_by(user_id=user.id).all()
    if not holidays:
        # Pre-populate with US federal holidays
        for date_str, name in US_FEDERAL_HOLIDAYS:
            h = Holiday(date=datetime.datetime.strptime(date_str, "%Y-%m-%d").date(), name=name, is_firm=True, user_id=user.id)
            db.session.add(h)
        db.session.commit()
        holidays = Holiday.query.filter_by(user_id=user.id).all()
    
    # Load vacation days
    vacation_days = VacationDay.query.filter_by(user_id=user.id).all()
    
    # Prepare data for template
    holiday_objs = [{"date": h.date.isoformat(), "name": h.name} for h in holidays]
    vacation_objs = [{"date": v.date.isoformat()} for v in vacation_days]
    workload_weights = goal.workload_weights if goal.workload_weights else {m: 1.0 for m in MONTHS}
    annual_goal = goal.annual_goal

    if request.method == 'POST':
        # 1. Annual goal
        try:
            annual_goal = int(request.form.get('annual_goal'))
            goal.annual_goal = annual_goal
        except Exception:
            flash('Invalid annual goal.', 'danger')
            return redirect(url_for('planner.setup_wizard'))
        
        # 2. Holidays
        # Remove unchecked holidays
        new_holidays = []
        for idx, h in enumerate(holidays):
            if not request.form.get(f'remove_holiday_{idx}'):
                date_val = request.form.getlist('holiday_dates')[idx]
                name_val = request.form.getlist('holiday_names')[idx]
                h.date = datetime.datetime.strptime(date_val, "%Y-%m-%d").date()
                h.name = name_val
                new_holidays.append(h)
            else:
                db.session.delete(h)
        # Add new holiday if provided
        new_holiday_date = request.form.get('new_holiday_date')
        new_holiday_name = request.form.get('new_holiday_name')
        if new_holiday_date and new_holiday_name:
            h = Holiday(date=datetime.datetime.strptime(new_holiday_date, "%Y-%m-%d").date(), name=new_holiday_name, is_firm=False, user_id=user.id)
            db.session.add(h)
        db.session.commit()

        # 3. Vacation days
        existing_vacations = VacationDay.query.filter_by(user_id=user.id).all()
        for idx, v in enumerate(existing_vacations):
            if not request.form.get(f'remove_vacation_{idx}'):
                date_val = request.form.getlist('vacation_dates')[idx]
                v.date = datetime.datetime.strptime(date_val, "%Y-%m-%d").date()
            else:
                db.session.delete(v)
        new_vacation_date = request.form.get('new_vacation_date')
        if new_vacation_date:
            v = VacationDay(date=datetime.datetime.strptime(new_vacation_date, "%Y-%m-%d").date(), user_id=user.id)
            db.session.add(v)
        db.session.commit()

        # 4. Monthly workload
        weights = {}
        for m in MONTHS:
            val = float(request.form.get(f'workload_{m}', 1.0))
            weights[m] = val
        goal.workload_weights = weights
        db.session.commit()

        flash('Setup saved!', 'success')
        return redirect(url_for('planner.dashboard'))

    return render_template(
        'planner/setup.html',
        annual_goal=annual_goal,
        holidays=holiday_objs,
        vacation_days=vacation_objs,
        workload_weights=workload_weights
    )
