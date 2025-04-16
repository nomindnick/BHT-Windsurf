from flask import render_template, redirect, url_for, flash, request
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

@planner_bp.route('/', methods=['GET', 'POST'])
@login_required
def dashboard():
    user = current_user
    year = datetime.date.today().year
    goal = BillableHourGoal.query.filter_by(user_id=user.id, year=year).first()
    holidays = Holiday.query.filter_by(user_id=user.id).all()
    vacation_days = VacationDay.query.filter_by(user_id=user.id).all()
    if not goal:
        flash('Please complete your setup wizard first.', 'warning')
        return redirect(url_for('planner.setup_wizard'))
    plan, monthly_targets = generate_plan(goal, holidays, vacation_days, goal.workload_weights)
    today = datetime.date.today()
    this_month = MONTHS[today.month - 1]
    daily_plan = {d: h for d, h in plan.items() if d.month == today.month}

    # Handle logging hours
    if request.method == 'POST':
        log_date = request.form.get('log_date')
        log_hours = request.form.get('log_hours')
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
        return redirect(url_for('planner.dashboard'))

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

    return render_template('planner/dashboard.html', 
        monthly_targets=monthly_targets, 
        daily_plan=daily_plan, 
        this_month=this_month,
        logs_by_date=logs_by_date,
        month_actual=month_actual,
        month_target=month_target,
        year_actual=year_actual,
        year_target=year_target,
        pace_status=pace_status,
        catchup_per_day=catchup_per_day,
        today=today
    )

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
