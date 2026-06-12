import sqlite3
import json
import os
from typing import List, Dict, Optional, Any
from datetime import datetime


class DatabaseService:
    def __init__(self, db_path: str = "agent.db"):
        self.db_path = db_path
        self._init_db()

    def _get_conn(self):
        conn = sqlite3.connect(self.db_path)
        conn.row_factory = sqlite3.Row
        return conn

    def _init_db(self):
        conn = self._get_conn()
        cursor = conn.cursor()

        cursor.execute('''
        CREATE TABLE IF NOT EXISTS enterprises (
            id INTEGER PRIMARY KEY AUTOINCREMENT,
            name TEXT NOT NULL UNIQUE,
            credit_code TEXT,
            legal_representative TEXT,
            registered_capital TEXT,
            establishment_date TEXT,
            business_status TEXT,
            industry TEXT,
            business_scope TEXT,
            address TEXT,
            registration_authority TEXT,
            annual_revenue TEXT,
            employee_count TEXT,
            registered_years TEXT,
            industry_category TEXT,
            data_source TEXT,
            created_at TEXT,
            updated_at TEXT
        )
        ''')

        cursor.execute('''
        CREATE TABLE IF NOT EXISTS credit_applications (
            id INTEGER PRIMARY KEY AUTOINCREMENT,
            enterprise_name TEXT NOT NULL,
            credit_type TEXT,
            application_amount REAL,
            application_period TEXT,
            fund_purpose TEXT,
            status TEXT DEFAULT 'draft',
            risk_level TEXT,
            total_score REAL,
            scorecard_json TEXT,
            credit_suggestion_json TEXT,
            report_json TEXT,
            created_at TEXT,
            updated_at TEXT
        )
        ''')

        cursor.execute('''
        CREATE TABLE IF NOT EXISTS conversation_history (
            id INTEGER PRIMARY KEY AUTOINCREMENT,
            session_id TEXT,
            enterprise_name TEXT,
            role TEXT,
            content TEXT,
            created_at TEXT
        )
        ''')

        conn.commit()
        conn.close()

    # ===== 企业信息 =====
    def save_enterprise(self, company_data: Dict[str, Any]) -> int:
        conn = self._get_conn()
        cursor = conn.cursor()
        now = datetime.now().isoformat()

        try:
            cursor.execute('SELECT id FROM enterprises WHERE name = ?', (company_data.get('name'),))
            existing = cursor.fetchone()

            if existing:
                cursor.execute('''
                UPDATE enterprises SET
                    credit_code=?, legal_representative=?, registered_capital=?,
                    establishment_date=?, business_status=?, industry=?,
                    business_scope=?, address=?, registration_authority=?,
                    annual_revenue=?, employee_count=?, registered_years=?,
                    industry_category=?, data_source=?, updated_at=?
                WHERE name=?
                ''', (
                    company_data.get('credit_code'),
                    company_data.get('legal_representative'),
                    company_data.get('registered_capital'),
                    company_data.get('establishment_date'),
                    company_data.get('business_status'),
                    company_data.get('industry'),
                    company_data.get('business_scope'),
                    company_data.get('address'),
                    company_data.get('registration_authority'),
                    company_data.get('annual_revenue'),
                    company_data.get('employee_count'),
                    company_data.get('registered_years'),
                    company_data.get('industry_category'),
                    company_data.get('data_source', '本地库'),
                    now,
                    company_data.get('name')
                ))
                enterprise_id = existing['id']
            else:
                cursor.execute('''
                INSERT INTO enterprises (
                    name, credit_code, legal_representative, registered_capital,
                    establishment_date, business_status, industry, business_scope,
                    address, registration_authority, annual_revenue, employee_count,
                    registered_years, industry_category, data_source, created_at, updated_at
                ) VALUES (?, ?, ?, ?, ?, ?, ?, ?, ?, ?, ?, ?, ?, ?, ?, ?, ?)
                ''', (
                    company_data.get('name'),
                    company_data.get('credit_code'),
                    company_data.get('legal_representative'),
                    company_data.get('registered_capital'),
                    company_data.get('establishment_date'),
                    company_data.get('business_status'),
                    company_data.get('industry'),
                    company_data.get('business_scope'),
                    company_data.get('address'),
                    company_data.get('registration_authority'),
                    company_data.get('annual_revenue'),
                    company_data.get('employee_count'),
                    company_data.get('registered_years'),
                    company_data.get('industry_category'),
                    company_data.get('data_source', '本地库'),
                    now,
                    now
                ))
                enterprise_id = cursor.lastrowid

            conn.commit()
            return enterprise_id
        finally:
            conn.close()

    def get_enterprise(self, name: str) -> Optional[Dict[str, Any]]:
        conn = self._get_conn()
        cursor = conn.cursor()
        cursor.execute('SELECT * FROM enterprises WHERE name = ?', (name,))
        row = cursor.fetchone()
        conn.close()
        if row:
            return dict(row)
        return None

    def list_enterprises(self) -> List[str]:
        conn = self._get_conn()
        cursor = conn.cursor()
        cursor.execute('SELECT name FROM enterprises ORDER BY updated_at DESC')
        rows = cursor.fetchall()
        conn.close()
        return [row['name'] for row in rows]

    # ===== 授信申请单 =====
    def save_credit_application(self, data: Dict[str, Any]) -> int:
        conn = self._get_conn()
        cursor = conn.cursor()
        now = datetime.now().isoformat()

        try:
            cursor.execute('SELECT id FROM credit_applications WHERE enterprise_name = ? AND status = ?',
                           (data.get('enterprise_name'), 'draft'))
            existing = cursor.fetchone()

            scorecard_json = json.dumps(data.get('scorecard', {}), ensure_ascii=False) if data.get('scorecard') else None
            credit_json = json.dumps(data.get('credit_suggestion', {}), ensure_ascii=False) if data.get('credit_suggestion') else None
            report_json = json.dumps(data.get('report', {}), ensure_ascii=False) if data.get('report') else None

            if existing:
                cursor.execute('''
                UPDATE credit_applications SET
                    credit_type=?, application_amount=?, application_period=?,
                    fund_purpose=?, status=?, risk_level=?, total_score=?,
                    scorecard_json=?, credit_suggestion_json=?, report_json=?,
                    updated_at=?
                WHERE id=?
                ''', (
                    data.get('credit_type'),
                    data.get('application_amount'),
                    data.get('application_period'),
                    data.get('fund_purpose'),
                    data.get('status', 'draft'),
                    data.get('risk_level'),
                    data.get('total_score'),
                    scorecard_json,
                    credit_json,
                    report_json,
                    now,
                    existing['id']
                ))
                app_id = existing['id']
            else:
                cursor.execute('''
                INSERT INTO credit_applications (
                    enterprise_name, credit_type, application_amount, application_period,
                    fund_purpose, status, risk_level, total_score,
                    scorecard_json, credit_suggestion_json, report_json, created_at, updated_at
                ) VALUES (?, ?, ?, ?, ?, ?, ?, ?, ?, ?, ?, ?, ?)
                ''', (
                    data.get('enterprise_name'),
                    data.get('credit_type'),
                    data.get('application_amount'),
                    data.get('application_period'),
                    data.get('fund_purpose'),
                    data.get('status', 'draft'),
                    data.get('risk_level'),
                    data.get('total_score'),
                    scorecard_json,
                    credit_json,
                    report_json,
                    now,
                    now
                ))
                app_id = cursor.lastrowid

            conn.commit()
            return app_id
        finally:
            conn.close()

    def get_credit_application(self, enterprise_name: str) -> Optional[Dict[str, Any]]:
        conn = self._get_conn()
        cursor = conn.cursor()
        cursor.execute('SELECT * FROM credit_applications WHERE enterprise_name = ? ORDER BY updated_at DESC',
                       (enterprise_name,))
        row = cursor.fetchone()
        conn.close()
        if row:
            result = dict(row)
            for key in ['scorecard_json', 'credit_suggestion_json', 'report_json']:
                if result.get(key):
                    try:
                        result[key.replace('_json', '')] = json.loads(result[key])
                    except:
                        pass
            return result
        return None

    def list_credit_applications(self) -> List[Dict[str, Any]]:
        conn = self._get_conn()
        cursor = conn.cursor()
        cursor.execute('SELECT * FROM credit_applications ORDER BY updated_at DESC')
        rows = cursor.fetchall()
        conn.close()
        results = []
        for row in rows:
            result = dict(row)
            for key in ['scorecard_json', 'credit_suggestion_json', 'report_json']:
                if result.get(key):
                    try:
                        result[key.replace('_json', '')] = json.loads(result[key])
                    except:
                        pass
            results.append(result)
        return results

    def update_application_status(self, application_id: int, status: str, **kwargs) -> bool:
        conn = self._get_conn()
        cursor = conn.cursor()
        now = datetime.now().isoformat()

        try:
            update_fields = ['status=?', 'updated_at=?']
            params = [status, now]

            if 'credit_type' in kwargs:
                update_fields.append('credit_type=?')
                params.append(kwargs['credit_type'])
            if 'application_amount' in kwargs:
                update_fields.append('application_amount=?')
                params.append(kwargs['application_amount'])
            if 'application_period' in kwargs:
                update_fields.append('application_period=?')
                params.append(kwargs['application_period'])
            if 'fund_purpose' in kwargs:
                update_fields.append('fund_purpose=?')
                params.append(kwargs['fund_purpose'])

            params.append(application_id)

            cursor.execute(f'UPDATE credit_applications SET {", ".join(update_fields)} WHERE id=?', params)
            conn.commit()
            return cursor.rowcount > 0
        finally:
            conn.close()

    # ===== 对话历史 =====
    def save_message(self, session_id: str, enterprise_name: str, role: str, content: str):
        conn = self._get_conn()
        cursor = conn.cursor()
        now = datetime.now().isoformat()
        cursor.execute(
            'INSERT INTO conversation_history (session_id, enterprise_name, role, content, created_at) VALUES (?, ?, ?, ?, ?)',
            (session_id, enterprise_name, role, content, now)
        )
        conn.commit()
        conn.close()

    def get_conversation(self, session_id: str) -> List[Dict[str, Any]]:
        conn = self._get_conn()
        cursor = conn.cursor()
        cursor.execute('SELECT * FROM conversation_history WHERE session_id = ? ORDER BY id ASC', (session_id,))
        rows = cursor.fetchall()
        conn.close()
        return [dict(row) for row in rows]
