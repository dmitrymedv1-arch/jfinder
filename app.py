import streamlit as st
import requests
import pandas as pd
import numpy as np
import matplotlib.pyplot as plt
import matplotlib
matplotlib.use('Agg')
import plotly.express as px
import plotly.graph_objects as go
import re
import time
import json
import random
from datetime import datetime, timedelta
from collections import Counter, defaultdict
from typing import List, Dict, Tuple, Optional, Set, Any
import hashlib
from tenacity import retry, stop_after_attempt, wait_exponential, retry_if_exception_type
from ratelimit import limits, sleep_and_retry
import logging
import io
from pathlib import Path
import warnings
import base64
import os
warnings.filterwarnings('ignore')

# ============================================================================
# PAGE CONFIGURATION
# ============================================================================

st.set_page_config(
    page_title="Journal Recommender",
    page_icon="📚",
    layout="wide",
    initial_sidebar_state="expanded"
)

# ============================================================================
# CONSTANTS
# ============================================================================

CURRENT_YEAR = datetime.now().year
DEFAULT_YEARS = [CURRENT_YEAR - 2, CURRENT_YEAR - 1, CURRENT_YEAR]

# SDG (Sustainable Development Goals)
SDG_LIST = {
    '1': 'No Poverty',
    '2': 'Zero Hunger',
    '3': 'Good Health and Well-being',
    '4': 'Quality Education',
    '5': 'Gender Equality',
    '6': 'Clean Water and Sanitation',
    '7': 'Affordable and Clean Energy',
    '8': 'Decent Work and Economic Growth',
    '9': 'Industry, Innovation and Infrastructure',
    '10': 'Reduced Inequalities',
    '11': 'Sustainable Cities and Communities',
    '12': 'Responsible Consumption and Production',
    '13': 'Climate Action',
    '14': 'Life Below Water',
    '15': 'Life on Land',
    '16': 'Peace, Justice and Strong Institutions',
    '17': 'Partnerships for the Goals'
}

# Topic levels in OpenAlex
TOPIC_LEVELS = ['Topic', 'Subfield', 'Field', 'Domain', 'Concepts']

# ============================================================================
# LOGGING CONFIGURATION
# ============================================================================

logging.basicConfig(level=logging.INFO, format='%(asctime)s - %(levelname)s - %(message)s')
logger = logging.getLogger(__name__)

# ============================================================================
# OPENALEX API CONFIGURATION
# ============================================================================

OPENALEX_BASE_URL = "https://api.openalex.org"
MAILTO = "your-email@example.com"
POLITE_POOL_HEADER = {'User-Agent': f'Journal-Recommender (mailto:{MAILTO})'}

# Rate limit settings
RATE_LIMIT_PER_SECOND = 8
CURSOR_PAGE_SIZE = 200
MAX_RETRIES = 3
INITIAL_DELAY = 1
MAX_DELAY = 60

# ============================================================================
# LOCALIZATION
# ============================================================================

TEXTS = {
    'en': {
        'app_title': '📚 Journal Recommender',
        'app_subtitle': 'Find the most relevant journals for your research',
        'level1_label': 'Level 1 (Main field)',
        'level1_placeholder': 'e.g., "hydrogen energy", "artificial intelligence"',
        'level2_label': 'Level 2 (Refinement - optional)',
        'level2_placeholder': 'e.g., "high entropy oxides", "deep learning"',
        'years_label': '📅 Publication Period',
        'years_info': 'Fixed: Last 2 years ({start}-{end})',
        'min_papers_label': '📄 Minimum papers per journal',
        'min_papers_help': 'Journals with fewer papers will be filtered out',
        'max_results_label': '📊 Number of results',
        'max_results_help': 'How many top journals to show',
        'analyze_btn': '🔍 Analyze Journals',
        'analyzing': '⏳ Analyzing...',
        'error_no_level1': '❌ Please enter Level 1 term',
        'error_no_results': '❌ No journals found. Try adjusting your query.',
        'total_journals': 'Total Journals Found',
        'after_filtering': 'After Filtering',
        'oa_journals': 'Open Access',
        'stm_journals': 'STM Members',
        'rank': 'Rank',
        'journal': 'Journal',
        'publisher': 'Publisher',
        'publisher_type': 'Publisher Type',
        'oa_status': 'OA',
        'papers': 'Papers',
        'relevance': 'Relevance',
        'impact_factor': 'Impact Factor',
        'quartile': 'Quartile',
        'h_index': 'h-index',
        'countries': 'Countries',
        'topics': 'Topics',
        'homepage': 'Homepage',
        'issn': 'ISSN',
        'visit': 'Visit',
        'score': 'Score',
        'filter_by_quartile': '📊 Filter by Quartile',
        'filter_by_stm': '🏛️ Publisher Type',
        'filter_by_country': '🌍 Filter by Country',
        'filter_by_sdg': '🎯 Filter by SDG',
        'all_countries': 'All Countries',
        'all_sdg': 'All SDGs',
        'all_quartiles': 'All Quartiles',
        'stm_all': 'All Publishers',
        'stm_only': 'STM Members only',
        'stm_exclude': 'Non-STM only',
        'statistics': '📊 Statistics',
        'by_publisher': 'By Publisher',
        'by_oa_status': 'By OA Status',
        'by_quartile': 'By Quartile',
        'by_stm': 'By STM Status',
        'by_sdg': 'By SDG',
        'topic_hierarchy': '📚 Topic Hierarchy',
        'yes': 'Yes',
        'no': 'No',
        'not_available': 'N/A',
        'loading_jcr': 'Loading JCR data...',
        'jcr_not_found': 'JCR.xlsx not found. Impact Factor data will be unavailable.',
        'jcr_loaded': '✅ JCR data loaded: {count} journals',
        'generated': 'Generated',
        'query': 'Query',
        'period': 'Period',
        'html_report_title': 'Journal Recommendation Report',
        'html_total_journals': 'Total Journals Found',
        'html_after_filtering': 'After Filtering',
        'html_oa_journals': 'Open Access',
        'html_stm_journals': 'STM Members',
        'html_recommendations': 'Top {count} Recommended Journals',
        'html_statistics': 'Statistics',
        'html_by_publisher': 'By Publisher',
        'html_by_oa': 'By OA Status',
        'html_by_quartile': 'By Quartile',
        'html_publisher_type': 'Publisher Type',
        'html_count': 'Count',
        'html_percentage': 'Percentage',
        'html_footer': 'Generated by Journal Recommender powered by OpenAlex',
        'html_copyright': '© 2026 Journal Recommender Tool',
        'html_impact_factor': 'Impact Factor',
        'html_h_index': 'h-index',
        'html_relevance_score': 'Relevance Score',
        'html_composite_score': 'Composite Score',
        'html_open_access': 'Open Access',
        'html_subscription': 'Subscription',
        'html_countries': 'Countries',
        'html_topics': 'Topics',
        'html_domain': 'Domain',
        'html_field': 'Field',
        'html_subfield': 'Subfield',
        'html_concepts': 'Concepts',
        'html_sdg': 'SDG'
    },
    'ru': {
        'app_title': '📚 Рекомендатель журналов',
        'app_subtitle': 'Найдите наиболее релевантные журналы для вашего исследования',
        'level1_label': 'Уровень 1 (Основная область)',
        'level1_placeholder': 'например, "водородная энергетика", "искусственный интеллект"',
        'level2_label': 'Уровень 2 (Уточнение - опционально)',
        'level2_placeholder': 'например, "высокоэнтропийные оксиды", "глубокое обучение"',
        'years_label': '📅 Период публикаций',
        'years_info': 'Фиксированный: последние 2 года ({start}-{end})',
        'min_papers_label': '📄 Минимальное количество статей в журнале',
        'min_papers_help': 'Журналы с меньшим количеством статей будут исключены',
        'max_results_label': '📊 Количество результатов',
        'max_results_help': 'Сколько топ-журналов показывать',
        'analyze_btn': '🔍 Анализировать журналы',
        'analyzing': '⏳ Анализ...',
        'error_no_level1': '❌ Пожалуйста, введите термин Уровня 1',
        'error_no_results': '❌ Журналы не найдены. Попробуйте изменить запрос.',
        'total_journals': 'Всего найдено журналов',
        'after_filtering': 'После фильтрации',
        'oa_journals': 'Открытый доступ',
        'stm_journals': 'Члены STM',
        'rank': 'Место',
        'journal': 'Журнал',
        'publisher': 'Издатель',
        'publisher_type': 'Тип издателя',
        'oa_status': 'OA',
        'papers': 'Статьи',
        'relevance': 'Релевантность',
        'impact_factor': 'Импакт-фактор',
        'quartile': 'Квартиль',
        'h_index': 'h-индекс',
        'countries': 'Страны',
        'topics': 'Темы',
        'homepage': 'Сайт',
        'issn': 'ISSN',
        'visit': 'Перейти',
        'score': 'Балл',
        'filter_by_quartile': '📊 Фильтр по квартилям',
        'filter_by_stm': '🏛️ Тип издателя',
        'filter_by_country': '🌍 Фильтр по стране',
        'filter_by_sdg': '🎯 Фильтр по ЦУР',
        'all_countries': 'Все страны',
        'all_sdg': 'Все ЦУР',
        'all_quartiles': 'Все квартили',
        'stm_all': 'Все издатели',
        'stm_only': 'Только члены STM',
        'stm_exclude': 'Не члены STM',
        'statistics': '📊 Статистика',
        'by_publisher': 'По издателям',
        'by_oa_status': 'По типу доступа',
        'by_quartile': 'По квартилям',
        'by_stm': 'По статусу STM',
        'by_sdg': 'По ЦУР',
        'topic_hierarchy': '📚 Иерархия тем',
        'yes': 'Да',
        'no': 'Нет',
        'not_available': 'Н/Д',
        'loading_jcr': 'Загрузка данных JCR...',
        'jcr_not_found': 'JCR.xlsx не найден. Данные об импакт-факторе будут недоступны.',
        'jcr_loaded': '✅ Данные JCR загружены: {count} журналов',
        'generated': 'Сгенерирован',
        'query': 'Запрос',
        'period': 'Период',
        'html_report_title': 'Отчет о рекомендации журналов',
        'html_total_journals': 'Всего найдено журналов',
        'html_after_filtering': 'После фильтрации',
        'html_oa_journals': 'Открытый доступ',
        'html_stm_journals': 'Члены STM',
        'html_recommendations': 'Топ {count} рекомендуемых журналов',
        'html_statistics': 'Статистика',
        'html_by_publisher': 'По издателям',
        'html_by_oa': 'По типу доступа',
        'html_by_quartile': 'По квартилям',
        'html_publisher_type': 'Тип издателя',
        'html_count': 'Количество',
        'html_percentage': 'Процент',
        'html_footer': 'Сгенерировано рекомендателем журналов на основе OpenAlex',
        'html_copyright': '© 2026 Инструмент рекомендации журналов',
        'html_impact_factor': 'Импакт-фактор',
        'html_h_index': 'h-индекс',
        'html_relevance_score': 'Оценка релевантности',
        'html_composite_score': 'Композитный балл',
        'html_open_access': 'Открытый доступ',
        'html_subscription': 'По подписке',
        'html_countries': 'Страны',
        'html_topics': 'Темы',
        'html_domain': 'Домен',
        'html_field': 'Область',
        'html_subfield': 'Подобласть',
        'html_concepts': 'Концепты',
        'html_sdg': 'ЦУР'
    }
}

# ============================================================================
# LANGUAGE SELECTION
# ============================================================================

def get_text(key: str) -> str:
    """Get localized text"""
    lang = st.session_state.get('language', 'en')
    if lang == 'ru' and key in TEXTS['ru']:
        return TEXTS['ru'][key]
    elif key in TEXTS['en']:
        return TEXTS['en'][key]
    return key

# ============================================================================
# JCR DATA LOADER
# ============================================================================

@st.cache_data(ttl=3600)
def load_jcr_data() -> Optional[Dict]:
    """Load JCR data from Excel file"""
    try:
        if not os.path.exists("JCR.xlsx"):
            return None
        
        df = pd.read_excel("JCR.xlsx")
        jcr_data = {}
        
        for _, row in df.iterrows():
            journal_title = str(row.get('Journal Title', '')).strip()
            issn_print = str(row.get('ISSN (print)', '')).strip()
            issn_electronic = str(row.get('ISSN (electronic)', '')).strip()
            if_numeric = row.get('2025-IF', 0)
            quartile = str(row.get('Quartile', 'N/A')).strip()
            
            # Handle N/A values for IF
            if pd.isna(if_numeric) or if_numeric == '<0.1' or if_numeric == 'N/A':
                if_numeric = 0.0
            else:
                try:
                    if_numeric = float(if_numeric)
                except:
                    if_numeric = 0.0
            
            # Store by ISSN (both print and electronic)
            for issn in [issn_print, issn_electronic]:
                if issn and issn != 'nan' and issn != 'N/A':
                    # If multiple entries for same ISSN, keep the best quartile
                    if issn not in jcr_data or quartile_is_better(quartile, jcr_data[issn].get('quartile', 'N/A')):
                        jcr_data[issn] = {
                            'journal_title': journal_title,
                            'if': if_numeric,
                            'quartile': quartile
                        }
        
        logger.info(f"Loaded {len(jcr_data)} journals from JCR")
        return jcr_data
    except Exception as e:
        logger.error(f"Error loading JCR data: {e}")
        return None

def quartile_is_better(q1: str, q2: str) -> bool:
    """Determine if q1 is better (higher) than q2"""
    if q2 == 'N/A':
        return True
    if q1 == 'N/A':
        return False
    
    # Map quartiles to numeric values
    q_map = {'Q1': 1, 'Q2': 2, 'Q3': 3, 'Q4': 4}
    return q_map.get(q1, 5) < q_map.get(q2, 5)

def get_journal_metrics(journal_name: str, issns: List[str], jcr_data: Optional[Dict]) -> Dict:
    """Get impact factor and quartile for a journal by ISSN"""
    if not jcr_data:
        return {'if': 0.0, 'quartile': 'N/A'}
    
    # Ensure issns is a list
    if issns is None:
        issns = []
    
    best_if = 0.0
    best_quartile = 'N/A'
    
    for issn in issns:
        if issn and issn in jcr_data:
            data = jcr_data[issn]
            if data.get('if', 0) > best_if:
                best_if = data.get('if', 0)
            if quartile_is_better(data.get('quartile', 'N/A'), best_quartile):
                best_quartile = data.get('quartile', 'N/A')
    
    return {'if': best_if, 'quartile': best_quartile}

# ============================================================================
# PUBLISHER CLASSIFICATION
# ============================================================================

PUBLISHER_CLASSIFICATION = {
    'STM_MEGA': {
        'Elsevier': ['Elsevier', 'Elsevier B.V.', 'Elsevier Science'],
        'Springer Nature': ['Springer Nature', 'Springer', 'Nature Publishing Group'],
        'Wiley': ['John Wiley & Sons', 'Wiley-Blackwell', 'Wiley-VCH'],
        'Taylor & Francis': ['Taylor & Francis Group', 'Routledge'],
        'SAGE': ['SAGE Publishing', 'SAGE Publications'],
        'MDPI': ['MDPI AG', 'MDPI']
    },
    'UNIVERSITY_PRESSES': {
        'Oxford University Press': ['Oxford University Press'],
        'Cambridge University Press': ['Cambridge University Press'],
        'Harvard University Press': ['Harvard University Press'],
        'MIT Press': ['MIT Press'],
        'Stanford University Press': ['Stanford University Press'],
        'Yale University Press': ['Yale University Press']
    },
    'SCIENTIFIC_SOCIETIES': {
        'ACS': ['American Chemical Society'],
        'APS': ['American Physical Society'],
        'IEEE': ['IEEE', 'Institute of Electrical and Electronics Engineers'],
        'RSC': ['Royal Society of Chemistry'],
        'IOP': ['IOP Publishing'],
        'AIP': ['AIP Publishing'],
        'BMJ': ['BMJ Publishing Group'],
        'JAMA': ['American Medical Association'],
        'APA': ['American Psychological Association'],
        'ACM': ['Association for Computing Machinery']
    },
    'OA_SPECIALISTS': {
        'PLoS': ['PLoS', 'Public Library of Science'],
        'Frontiers': ['Frontiers Media'],
        'Hindawi': ['Hindawi'],
        'PeerJ': ['PeerJ'],
        'Cogent OA': ['Cogent OA']
    }
}

# STM Members list (for quick classification)
STM_MEMBERS = [
    'Elsevier', 'Springer Nature', 'John Wiley & Sons',
    'Taylor & Francis Group', 'SAGE Publishing', 'MDPI'
]

def classify_publisher(publisher_name: str) -> Dict:
    """Classify publisher into categories"""
    if not publisher_name:
        return {'category': 'OTHER', 'group': 'Unknown', 'is_stm': False}
    
    # Check STM members first
    for stm in STM_MEMBERS:
        if stm.lower() in publisher_name.lower():
            return {'category': 'STM_MEGA', 'group': stm, 'is_stm': True}
    
    # Check other categories
    for category, groups in PUBLISHER_CLASSIFICATION.items():
        for group_name, aliases in groups.items():
            for alias in aliases:
                if alias.lower() in publisher_name.lower():
                    return {
                        'category': category,
                        'group': group_name,
                        'is_stm': category == 'STM_MEGA'
                    }
    
    return {'category': 'OTHER', 'group': publisher_name, 'is_stm': False}

# ============================================================================
# TEXT PROCESSING
# ============================================================================

def clean_text(text: str) -> str:
    """Clean text from HTML tags and extra characters"""
    if not text:
        return ""
    text = re.sub(r'<[^>]+>', '', text)
    return text.strip()

def parse_query_terms(term: str) -> str:
    """Parse search term for OpenAlex API"""
    term = term.strip()
    if not term:
        return ""
    
    # If it's a quoted phrase, leave as is
    if term.startswith('"') and term.endswith('"'):
        return term
    
    # If there's OR operator
    if ' OR ' in term.upper():
        parts = re.split(r'\s+OR\s+', term, flags=re.IGNORECASE)
        processed_parts = []
        for part in parts:
            part = part.strip()
            if ' ' in part and not (part.startswith('"') and part.endswith('"')):
                processed_parts.append(f'"{part}"')
            else:
                processed_parts.append(part)
        return ' OR '.join(processed_parts)
    
    # If there are spaces, it's a phrase
    if ' ' in term:
        return f'"{term}"'
    
    return term

# ============================================================================
# OPENALEX API CLIENT
# ============================================================================

@retry(
    stop=stop_after_attempt(MAX_RETRIES),
    wait=wait_exponential(multiplier=INITIAL_DELAY, max=MAX_DELAY),
    retry=retry_if_exception_type((requests.exceptions.RequestException,))
)
@sleep_and_retry
@limits(calls=RATE_LIMIT_PER_SECOND, period=1)
def make_openalex_request(url: str, params: Optional[Dict] = None) -> Optional[Dict]:
    """Make request to OpenAlex API with rate limiting"""
    if params is None:
        params = {}
    
    params['mailto'] = MAILTO
    
    try:
        response = requests.get(
            url,
            params=params,
            headers=POLITE_POOL_HEADER,
            timeout=30
        )
        
        if response.status_code == 200:
            return response.json()
        elif response.status_code == 429:
            retry_after = int(response.headers.get('Retry-After', 5))
            logger.warning(f"Rate limited. Waiting {retry_after} seconds")
            time.sleep(retry_after)
            raise requests.exceptions.RequestException("Rate limited")
        else:
            logger.error(f"Error {response.status_code}: {response.text[:200]}")
            return None
            
    except requests.exceptions.Timeout:
        logger.warning("Request timeout")
        raise
    except Exception as e:
        logger.error(f"Request error: {str(e)}")
        raise

def search_works(level1: str, level2: Optional[str], years: List[int], limit: int = 500) -> List[Dict]:
    """Search works in OpenAlex matching the query"""
    # Build search query
    search_parts = []
    
    if level1:
        search_parts.append(parse_query_terms(level1))
    if level2:
        search_parts.append(parse_query_terms(level2))
    
    if not search_parts:
        return []
    
    query = ' AND '.join(search_parts)
    
    # Build filters
    filter_parts = [f'default.search:{query}']
    if years:
        filter_parts.append(f'publication_year:{min(years)}-{max(years)}')
    
    all_works = []
    cursor = "*"
    page = 0
    
    while len(all_works) < limit and cursor:
        page += 1
        params = {
            'filter': ','.join(filter_parts),
            'per-page': min(CURSOR_PAGE_SIZE, limit - len(all_works)),
            'cursor': cursor,
            'sort': 'relevance_score:desc'
        }
        
        data = make_openalex_request(f"{OPENALEX_BASE_URL}/works", params)
        
        if not data or 'results' not in data:
            break
        
        works = data['results']
        if not works:
            break
        
        all_works.extend(works)
        cursor = data.get('meta', {}).get('next_cursor')
        time.sleep(0.1)
    
    return all_works[:limit]

def enrich_work_data(work: Dict) -> Dict:
    """Enrich work data with additional fields"""
    if not work:
        return {}
    
    # Extract source (journal) information
    source = work.get('primary_location', {}).get('source', {})
    if not source:
        source = work.get('locations', [{}])[0].get('source', {})
    
    # Extract authors
    authorships = work.get('authorships', [])
    authors = []
    countries = set()
    institutions = []
    
    for authorship in authorships[:10]:
        if authorship and 'author' in authorship:
            author_name = authorship['author'].get('display_name', '')
            if author_name:
                authors.append(author_name)
        
        # Extract institution and country
        if authorship and 'institutions' in authorship:
            for inst in authorship.get('institutions', []):
                if inst.get('display_name'):
                    institutions.append(inst['display_name'])
                if inst.get('country_code'):
                    countries.add(inst['country_code'])
    
    # Extract ISSNs - FIXED: handle None
    issns = []
    if source:
        issn_list = source.get('issn')
        if issn_list is None:
            issns = []
        elif isinstance(issn_list, list):
            issns = issn_list
        elif isinstance(issn_list, str):
            issns = [issn_list]
    
    # Extract concepts with hierarchy
    concepts = []
    for concept in work.get('concepts', [])[:5]:
        if concept and concept.get('display_name'):
            concepts.append({
                'name': concept['display_name'],
                'score': concept.get('score', 0),
                'level': concept.get('level', 0)
            })
    
    # Extract topics (for Topic/Subfield/Field/Domain)
    topics_data = []
    for topic in work.get('topics', [])[:3]:
        if topic and topic.get('display_name'):
            topics_data.append({
                'name': topic.get('display_name', ''),
                'id': topic.get('id', ''),
                'subfield': topic.get('subfield', {}).get('display_name', '') if topic.get('subfield') else '',
                'field': topic.get('field', {}).get('display_name', '') if topic.get('field') else '',
                'domain': topic.get('domain', {}).get('display_name', '') if topic.get('domain') else ''
            })
    
    # Extract SDG (Sustainable Development Goals)
    sdg_list = []
    for sdg in work.get('sustainable_development_goals', [])[:3]:
        if sdg and sdg.get('display_name'):
            sdg_list.append(sdg.get('display_name', ''))
    
    # Get DOI safely
    doi = work.get('doi', '')
    if doi is None:
        doi = ''
    else:
        doi = str(doi).replace('https://doi.org/', '')
    
    return {
        'id': work.get('id', ''),
        'title': clean_text(work.get('title', '')),
        'publication_year': work.get('publication_year', 0),
        'cited_by_count': work.get('cited_by_count', 0),
        'relevance_score': work.get('relevance_score', 0),
        'doi': doi,
        'source_id': source.get('id', '') if source else '',
        'source_name': source.get('display_name', '') if source else '',
        'source_issn': issns,
        'source_publisher': source.get('publisher', '') if source else '',
        'source_host_organization': source.get('host_organization_name', '') if source else '',
        'source_is_oa': source.get('is_oa', False) if source else False,
        'source_homepage': source.get('homepage_url', '') if source else '',
        'authors': authors,
        'countries': list(countries),
        'institutions': institutions[:5],
        'concepts': concepts,
        'topics': topics_data,
        'sdg': sdg_list,
        'is_oa': work.get('open_access', {}).get('is_oa', False)
    }

def get_source_metadata(source_id: str) -> Dict:
    """Get detailed metadata for a source (journal)"""
    if not source_id:
        return {}
    
    # Extract ID from full URL if needed
    if source_id.startswith('https://openalex.org/'):
        source_id = source_id.replace('https://openalex.org/', '')
    
    url = f"{OPENALEX_BASE_URL}/sources/{source_id}"
    data = make_openalex_request(url)
    
    if data:
        return {
            'id': data.get('id', ''),
            'display_name': data.get('display_name', ''),
            'publisher': data.get('publisher', ''),
            'host_organization_name': data.get('host_organization_name', ''),
            'host_organization_lineage_names': data.get('host_organization_lineage_names', []),
            'is_oa': data.get('is_oa', False),
            'issn_l': data.get('issn_l', ''),
            'issn': data.get('issn', []),
            'works_count': data.get('works_count', 0),
            'cited_by_count': data.get('cited_by_count', 0),
            'homepage_url': data.get('homepage_url', ''),
            'topics': data.get('topics', []),
            'x_concepts': data.get('x_concepts', [])
        }
    
    return {}

# ============================================================================
# JOURNAL ANALYSIS
# ============================================================================

class JournalAnalyzer:
    """Class for analyzing journals from works data"""
    
    def __init__(self, works: List[Dict], min_papers: int = 3):
        self.works = works
        self.min_papers = min_papers
        self.journal_data = {}
        self.analyze()
    
    def analyze(self):
        """Analyze journals from works data"""
        # Group works by source
        source_works = defaultdict(list)
        for work in self.works:
            enriched = enrich_work_data(work)
            source_id = enriched.get('source_id', '')
            if source_id:
                source_works[source_id].append(enriched)
        
        # Analyze each source
        for source_id, works_list in source_works.items():
            if len(works_list) < self.min_papers:
                continue
            
            # Get source metadata
            source_meta = get_source_metadata(source_id)
            
            # Calculate metrics
            relevance_scores = [w.get('relevance_score', 0) for w in works_list]
            citations = [w.get('cited_by_count', 0) for w in works_list]
            years = [w.get('publication_year', 0) for w in works_list]
            
            # h-index calculation
            citations_sorted = sorted(citations, reverse=True)
            h_index = 0
            for i, cit in enumerate(citations_sorted, 1):
                if cit >= i:
                    h_index = i
                else:
                    break
            
            # Countries
            all_countries = set()
            for w in works_list:
                all_countries.update(w.get('countries', []))
            
            # Concepts - FIXED: handle None values
            all_concepts = Counter()
            for w in works_list:
                concepts = w.get('concepts', [])
                if concepts:
                    for concept in concepts:
                        if concept and concept.get('name'):
                            all_concepts[concept['name']] += 1
            
            # Topics hierarchy
            all_topics = []
            topic_hierarchy = {
                'topics': set(),
                'subfields': set(),
                'fields': set(),
                'domains': set()
            }
            all_sdg = set()
            
            for w in works_list:
                for topic in w.get('topics', []):
                    if topic.get('name'):
                        all_topics.append(topic['name'])
                        topic_hierarchy['topics'].add(topic['name'])
                    if topic.get('subfield'):
                        topic_hierarchy['subfields'].add(topic['subfield'])
                    if topic.get('field'):
                        topic_hierarchy['fields'].add(topic['field'])
                    if topic.get('domain'):
                        topic_hierarchy['domains'].add(topic['domain'])
                
                for sdg in w.get('sdg', []):
                    if sdg:
                        all_sdg.add(sdg)
            
            # Get ISSNs
            issns = source_meta.get('issn', [])
            if not issns or issns is None:
                issns = []
                # Try to get from works
                for w in works_list:
                    if w.get('source_issn'):
                        issns = w['source_issn']
                        break
            
            # Ensure issns is a list
            if issns is None:
                issns = []
            
            # Get JCR metrics
            jcr_data = st.session_state.get('jcr_data', None)
            jcr_metrics = get_journal_metrics(
                source_meta.get('display_name', ''),
                issns,
                jcr_data
            )
            
            # Classify publisher
            publisher_name = source_meta.get('publisher', '') or source_meta.get('host_organization_name', '')
            publisher_class = classify_publisher(publisher_name)
            
            self.journal_data[source_id] = {
                'source_id': source_id,
                'name': source_meta.get('display_name', works_list[0].get('source_name', 'Unknown')),
                'publisher': publisher_name,
                'publisher_class': publisher_class,
                'is_oa': source_meta.get('is_oa', works_list[0].get('source_is_oa', False)),
                'issn': issns,
                'homepage_url': source_meta.get('homepage_url', works_list[0].get('source_homepage', '')),
                'works_count': len(works_list),
                'cited_by_count': source_meta.get('cited_by_count', sum(citations)),
                'relevance_score': np.mean(relevance_scores) if relevance_scores else 0,
                'h_index': h_index,
                'avg_citations': np.mean(citations) if citations else 0,
                'median_citations': np.median(citations) if citations else 0,
                'max_citations': max(citations) if citations else 0,
                'years': years,
                'countries': list(all_countries),
                'top_concepts': all_concepts.most_common(10),
                'topics': list(topic_hierarchy['topics'])[:5],
                'subfields': list(topic_hierarchy['subfields'])[:5],
                'fields': list(topic_hierarchy['fields'])[:5],
                'domains': list(topic_hierarchy['domains'])[:5],
                'sdg': list(all_sdg)[:5],
                'works': works_list,
                'impact_factor': jcr_metrics.get('if', 0),
                'quartile': jcr_metrics.get('quartile', 'N/A')
            }
    
    def get_journals(self) -> Dict:
        """Get analyzed journal data"""
        return self.journal_data
    
    def get_available_countries(self) -> List[str]:
        """Get list of all countries found in journals"""
        countries = set()
        for data in self.journal_data.values():
            countries.update(data.get('countries', []))
        return sorted(list(countries))
    
    def get_available_sdg(self) -> List[str]:
        """Get list of all SDG found in journals"""
        sdg_set = set()
        for data in self.journal_data.values():
            sdg_set.update(data.get('sdg', []))
        return sorted(list(sdg_set))
    
    def filter_by_quartile(self, selected_quartiles: List[str]) -> Dict:
        """Filter journals by quartile"""
        if not selected_quartiles or 'All' in selected_quartiles:
            return self.journal_data
        
        filtered = {}
        for source_id, data in self.journal_data.items():
            quartile = data.get('quartile', 'N/A')
            if quartile in selected_quartiles:
                filtered[source_id] = data
        return filtered
    
    def filter_by_stm(self, stm_filter: str) -> Dict:
        """Filter journals by STM status"""
        if stm_filter == 'all':
            return self.journal_data
        
        filtered = {}
        for source_id, data in self.journal_data.items():
            is_stm = data.get('publisher_class', {}).get('is_stm', False)
            if stm_filter == 'stm_only' and is_stm:
                filtered[source_id] = data
            elif stm_filter == 'non_stm' and not is_stm:
                filtered[source_id] = data
        return filtered
    
    def filter_by_country(self, country: str) -> Dict:
        """Filter journals by country"""
        if not country or country == 'All':
            return self.journal_data
        
        filtered = {}
        for source_id, data in self.journal_data.items():
            if country in data.get('countries', []):
                filtered[source_id] = data
        return filtered
    
    def filter_by_sdg(self, sdg: str) -> Dict:
        """Filter journals by SDG"""
        if not sdg or sdg == 'All':
            return self.journal_data
        
        filtered = {}
        for source_id, data in self.journal_data.items():
            if sdg in data.get('sdg', []):
                filtered[source_id] = data
        return filtered

def calculate_composite_score(journal: Dict) -> float:
    """Calculate composite score for ranking"""
    # Normalize metrics
    max_relevance = 1.0  # Relevance is already 0-1
    max_papers = 100  # Cap at 100 papers
    max_if = 20  # Cap at 20 IF
    max_h_index = 50  # Cap at 50 h-index
    max_years = 3  # Last 3 years
    
    relevance_norm = min(journal.get('relevance_score', 0) / max_relevance, 1.0)
    papers_norm = min(journal.get('works_count', 0) / max_papers, 1.0)
    if_norm = min(journal.get('impact_factor', 0) / max_if, 1.0)
    h_norm = min(journal.get('h_index', 0) / max_h_index, 1.0)
    
    # Recency: % of papers from last 2 years
    years = journal.get('years', [])
    if years:
        current_year = datetime.now().year
        recent = sum(1 for y in years if y >= current_year - 1)
        recency_norm = min(recent / max(len(years), 1), 1.0)
    else:
        recency_norm = 0
    
    # Composite score with weights
    score = (
        relevance_norm * 0.35 +
        papers_norm * 0.15 +
        if_norm * 0.20 +
        h_norm * 0.15 +
        recency_norm * 0.15
    )
    
    return min(score, 1.0)

# ============================================================================
# HTML REPORT GENERATOR (ENHANCED)
# ============================================================================

class ReportGenerator:
    """Class for generating enhanced HTML reports"""
    
    def __init__(self, journals: List[Dict], query_info: Dict, stats: Dict, lang: str = 'en'):
        self.journals = journals
        self.query_info = query_info
        self.stats = stats
        self.lang = lang
    
    def t(self, key: str) -> str:
        """Get localized text"""
        if self.lang == 'ru' and key in TEXTS['ru']:
            return TEXTS['ru'][key]
        return TEXTS['en'].get(key, key)
    
    def generate(self) -> str:
        """Generate enhanced HTML report"""
        primary_color = '#667eea'
        secondary_color = '#f39c12'
        accent_color = '#2d3436'
        
        # Build journal cards
        journal_cards = self._generate_journal_cards()
        
        # Build statistics
        stats_html = self._generate_statistics()
        
        # Build full HTML
        html = f"""<!DOCTYPE html>
<html lang="{self.lang}">
<head>
    <meta charset="UTF-8">
    <meta name="viewport" content="width=device-width, initial-scale=1.0">
    <title>{self.t('html_report_title')}</title>
    <style>
        /* ===== RESET & BASE ===== */
        * {{ margin: 0; padding: 0; box-sizing: border-box; }}
        body {{
            font-family: -apple-system, BlinkMacSystemFont, 'Segoe UI', Roboto, 'Helvetica Neue', Arial, sans-serif;
            background: #f0f2f5;
            padding: 30px 20px;
            color: #2d3436;
        }}
        .container {{
            max-width: 1400px;
            margin: 0 auto;
            background: #ffffff;
            border-radius: 20px;
            box-shadow: 0 20px 60px rgba(0,0,0,0.08);
            overflow: hidden;
        }}
        
        /* ===== HEADER ===== */
        .header {{
            background: linear-gradient(135deg, {primary_color} 0%, {secondary_color} 100%);
            padding: 45px 50px 40px;
            color: white;
            position: relative;
            overflow: hidden;
        }}
        .header::after {{
            content: '';
            position: absolute;
            top: -50%;
            right: -10%;
            width: 400px;
            height: 400px;
            background: rgba(255,255,255,0.05);
            border-radius: 50%;
        }}
        .header h1 {{
            font-size: 32px;
            font-weight: 700;
            margin-bottom: 8px;
            letter-spacing: -0.5px;
            position: relative;
            z-index: 1;
        }}
        .header .subtitle {{
            font-size: 16px;
            opacity: 0.9;
            margin-bottom: 15px;
            position: relative;
            z-index: 1;
        }}
        .header .meta {{
            display: flex;
            flex-wrap: wrap;
            gap: 20px 40px;
            font-size: 14px;
            opacity: 0.9;
            position: relative;
            z-index: 1;
            background: rgba(0,0,0,0.1);
            padding: 15px 20px;
            border-radius: 12px;
            margin-top: 10px;
        }}
        .header .meta-item {{
            display: flex;
            align-items: center;
            gap: 8px;
        }}
        .header .meta-item strong {{
            font-weight: 600;
        }}
        
        /* ===== STATS GRID ===== */
        .stats-grid {{
            display: grid;
            grid-template-columns: repeat(auto-fit, minmax(180px, 1fr));
            gap: 15px;
            padding: 30px 50px 20px;
            background: #fafbfc;
            border-bottom: 1px solid #eef1f4;
        }}
        .stat-card {{
            background: white;
            border-radius: 14px;
            padding: 18px 20px;
            text-align: center;
            box-shadow: 0 2px 8px rgba(0,0,0,0.04);
            transition: transform 0.2s, box-shadow 0.2s;
        }}
        .stat-card:hover {{
            transform: translateY(-2px);
            box-shadow: 0 4px 16px rgba(0,0,0,0.08);
        }}
        .stat-number {{
            font-size: 30px;
            font-weight: 700;
            background: linear-gradient(135deg, {primary_color} 0%, {secondary_color} 100%);
            -webkit-background-clip: text;
            -webkit-text-fill-color: transparent;
            background-clip: text;
        }}
        .stat-label {{
            font-size: 13px;
            color: #7f8c8d;
            margin-top: 4px;
            font-weight: 500;
        }}
        .stat-percent {{
            font-size: 12px;
            color: #2ecc71;
            font-weight: 600;
        }}
        
        /* ===== SECTION TITLE ===== */
        .section-title {{
            font-size: 22px;
            font-weight: 700;
            padding: 25px 50px 15px;
            color: {accent_color};
            display: flex;
            align-items: center;
            gap: 12px;
        }}
        .section-title .badge {{
            font-size: 13px;
            font-weight: 600;
            background: {primary_color};
            color: white;
            padding: 2px 14px;
            border-radius: 20px;
        }}
        
        /* ===== JOURNAL CARDS ===== */
        .journal-list {{
            padding: 0 50px 30px;
        }}
        .journal-card {{
            background: #fafbfc;
            border-radius: 16px;
            padding: 24px 28px;
            margin-bottom: 18px;
            border-left: 5px solid {primary_color};
            transition: all 0.3s ease;
            position: relative;
        }}
        .journal-card:hover {{
            transform: translateX(6px);
            box-shadow: 0 6px 24px rgba(0,0,0,0.06);
            background: #f8f9fa;
        }}
        .journal-header {{
            display: flex;
            align-items: center;
            flex-wrap: wrap;
            gap: 15px;
            margin-bottom: 14px;
        }}
        .journal-rank {{
            font-size: 16px;
            font-weight: 700;
            color: {primary_color};
            background: white;
            padding: 4px 14px;
            border-radius: 30px;
            box-shadow: 0 2px 8px rgba(0,0,0,0.06);
            min-width: 50px;
            text-align: center;
        }}
        .journal-name {{
            font-size: 19px;
            font-weight: 600;
            color: {accent_color};
            flex: 1;
        }}
        .journal-score {{
            font-size: 20px;
            font-weight: 700;
            padding: 4px 16px;
            border-radius: 30px;
            background: white;
            box-shadow: 0 2px 8px rgba(0,0,0,0.06);
        }}
        .score-high {{ color: #27ae60; }}
        .score-mid {{ color: #f39c12; }}
        .score-low {{ color: #e74c3c; }}
        
        .journal-metrics {{
            display: grid;
            grid-template-columns: repeat(auto-fit, minmax(130px, 1fr));
            gap: 12px;
            margin-bottom: 14px;
            padding: 12px 16px;
            background: white;
            border-radius: 12px;
        }}
        .metric {{
            display: flex;
            flex-direction: column;
        }}
        .metric-label {{
            font-size: 11px;
            color: #95a5a6;
            text-transform: uppercase;
            letter-spacing: 0.3px;
            font-weight: 600;
        }}
        .metric-value {{
            font-size: 16px;
            font-weight: 600;
            color: {accent_color};
        }}
        .metric-value .small {{
            font-size: 12px;
            font-weight: 400;
            color: #7f8c8d;
        }}
        
        .journal-details {{
            display: grid;
            grid-template-columns: 1fr 1fr;
            gap: 8px 30px;
            font-size: 14px;
            padding: 12px 16px;
            background: white;
            border-radius: 12px;
        }}
        .detail {{
            display: flex;
            align-items: baseline;
            gap: 6px;
            flex-wrap: wrap;
        }}
        .detail-label {{
            color: #95a5a6;
            font-weight: 500;
            font-size: 13px;
        }}
        .detail-value {{
            color: {accent_color};
            font-weight: 500;
        }}
        
        .badge {{
            display: inline-block;
            padding: 2px 12px;
            border-radius: 20px;
            font-size: 11px;
            font-weight: 600;
            margin-left: 4px;
        }}
        .badge-stm {{ background: #e3f2fd; color: #1565c0; }}
        .badge-oa {{ background: #e8f5e9; color: #2e7d32; }}
        .badge-sub {{ background: #fce4ec; color: #c62828; }}
        .badge-q1 {{ background: #e8f5e9; color: #1b5e20; }}
        .badge-q2 {{ background: #e3f2fd; color: #0d47a1; }}
        .badge-q3 {{ background: #fff3e0; color: #e65100; }}
        .badge-q4 {{ background: #fce4ec; color: #b71c1c; }}
        .badge-na {{ background: #eceff1; color: #546e7a; }}
        
        .clickable-link {{
            color: {primary_color};
            text-decoration: none;
            font-weight: 500;
            transition: color 0.2s;
        }}
        .clickable-link:hover {{
            color: {secondary_color};
            text-decoration: underline;
        }}
        
        /* ===== STATISTICS SECTION ===== */
        .stats-section {{
            padding: 20px 50px 40px;
            border-top: 1px solid #eef1f4;
            background: #fafbfc;
        }}
        .stats-grid-3 {{
            display: grid;
            grid-template-columns: repeat(auto-fit, minmax(200px, 1fr));
            gap: 20px;
            margin-top: 15px;
        }}
        .stats-grid-4 {{
            display: grid;
            grid-template-columns: repeat(auto-fit, minmax(150px, 1fr));
            gap: 15px;
            margin-top: 15px;
        }}
        .stat-card-small {{
            background: white;
            border-radius: 12px;
            padding: 16px 20px;
            text-align: center;
            box-shadow: 0 2px 8px rgba(0,0,0,0.04);
        }}
        .stat-card-small .num {{
            font-size: 24px;
            font-weight: 700;
            color: {primary_color};
        }}
        .stat-card-small .label {{
            font-size: 13px;
            color: #7f8c8d;
            margin-top: 4px;
        }}
        
        .publisher-grid {{
            display: grid;
            grid-template-columns: 1fr 1fr;
            gap: 8px 30px;
            margin-top: 10px;
        }}
        .publisher-item {{
            display: flex;
            align-items: center;
            gap: 12px;
            font-size: 14px;
            padding: 6px 10px;
            border-radius: 8px;
            background: white;
        }}
        .publisher-name {{
            min-width: 140px;
            font-weight: 500;
            color: {accent_color};
        }}
        .publisher-count {{
            min-width: 50px;
            color: #7f8c8d;
            font-weight: 600;
        }}
        .progress-bar {{
            flex: 1;
            height: 6px;
            background: #ecf0f1;
            border-radius: 4px;
            overflow: hidden;
        }}
        .progress-fill {{
            height: 100%;
            background: linear-gradient(90deg, {primary_color}, {secondary_color});
            border-radius: 4px;
            transition: width 0.6s ease;
        }}
        
        /* ===== TOPIC HIERARCHY ===== */
        .topic-hierarchy {{
            display: grid;
            grid-template-columns: repeat(auto-fit, minmax(200px, 1fr));
            gap: 15px;
            margin-top: 15px;
        }}
        .topic-level {{
            background: white;
            border-radius: 12px;
            padding: 14px 18px;
            box-shadow: 0 2px 8px rgba(0,0,0,0.04);
        }}
        .topic-level .level-name {{
            font-size: 13px;
            font-weight: 600;
            color: {primary_color};
            text-transform: uppercase;
            letter-spacing: 0.5px;
            margin-bottom: 6px;
        }}
        .topic-level .level-items {{
            font-size: 14px;
            color: {accent_color};
        }}
        .topic-level .level-items .item {{
            display: inline-block;
            background: #f0f2f5;
            padding: 2px 12px;
            border-radius: 15px;
            margin: 3px 4px 3px 0;
            font-size: 12px;
        }}
        
        /* ===== FOOTER ===== */
        .footer {{
            text-align: center;
            padding: 25px 50px;
            color: #95a5a6;
            font-size: 13px;
            border-top: 1px solid #eef1f4;
            background: #fafbfc;
        }}
        .footer a {{
            color: {primary_color};
            text-decoration: none;
        }}
        
        /* ===== RESPONSIVE ===== */
        @media (max-width: 768px) {{
            .header {{ padding: 30px 25px; }}
            .header h1 {{ font-size: 24px; }}
            .stats-grid {{ padding: 20px 25px; grid-template-columns: 1fr 1fr; }}
            .journal-list {{ padding: 0 25px 20px; }}
            .journal-card {{ padding: 18px 20px; }}
            .journal-details {{ grid-template-columns: 1fr; }}
            .journal-metrics {{ grid-template-columns: 1fr 1fr; }}
            .section-title {{ padding: 20px 25px 10px; font-size: 18px; }}
            .stats-section {{ padding: 20px 25px 30px; }}
            .publisher-grid {{ grid-template-columns: 1fr; }}
            .meta {{ flex-direction: column; gap: 8px; }}
        }}
        @media print {{
            body {{ background: white; padding: 0; }}
            .container {{ box-shadow: none; border-radius: 0; }}
            .journal-card:hover {{ transform: none; box-shadow: none; }}
            .stat-card:hover {{ transform: none; box-shadow: none; }}
        }}
    </style>
</head>
<body>
    <div class="container">
        <!-- HEADER -->
        <div class="header">
            <h1>{self.t('html_report_title')}</h1>
            <div class="subtitle">{self.t('app_subtitle')}</div>
            <div class="meta">
                <span class="meta-item"><strong>{self.t('query')}:</strong> {self.query_info.get('level1', '')}{' + ' + self.query_info.get('level2', '') if self.query_info.get('level2') else ''}</span>
                <span class="meta-item"><strong>{self.t('period')}:</strong> {self.query_info.get('years', [])}</span>
                <span class="meta-item"><strong>{self.t('generated')}:</strong> {datetime.now().strftime('%Y-%m-%d %H:%M')}</span>
            </div>
        </div>
        
        <!-- STATS -->
        <div class="stats-grid">
            <div class="stat-card">
                <div class="stat-number">{self.stats.get('total_found', 0)}</div>
                <div class="stat-label">{self.t('html_total_journals')}</div>
            </div>
            <div class="stat-card">
                <div class="stat-number">{self.stats.get('total_filtered', 0)}</div>
                <div class="stat-label">{self.t('html_after_filtering')}</div>
            </div>
            <div class="stat-card">
                <div class="stat-number">{self.stats.get('oa_count', 0)}</div>
                <div class="stat-label">{self.t('html_oa_journals')}</div>
            </div>
            <div class="stat-card">
                <div class="stat-number">{self.stats.get('stm_count', 0)}</div>
                <div class="stat-label">{self.t('html_stm_journals')}</div>
            </div>
        </div>
        
        <!-- RECOMMENDATIONS -->
        <div class="section-title">
            {self.t('html_recommendations').format(count=len(self.journals))}
            <span class="badge">{len(self.journals)}</span>
        </div>
        
        <div class="journal-list">
            {journal_cards}
        </div>
        
        <!-- STATISTICS -->
        {stats_html}
        
        <!-- FOOTER -->
        <div class="footer">
            {self.t('html_footer')}<br>
            {self.t('html_copyright')}
        </div>
    </div>
</body>
</html>"""
        
        return html
    
    def _generate_journal_cards(self) -> str:
        """Generate HTML for journal cards"""
        cards = ""
        for i, journal in enumerate(self.journals, 1):
            score = journal.get('composite_score', 0)
            score_pct = f"{score * 100:.1f}%"
            
            # Score color class
            if score >= 0.7:
                score_class = 'score-high'
            elif score >= 0.4:
                score_class = 'score-mid'
            else:
                score_class = 'score-low'
            
            # Publisher badge
            pub_class = journal.get('publisher_class', {})
            is_stm = pub_class.get('is_stm', False)
            stm_badge = '<span class="badge badge-stm">STM</span>' if is_stm else ''
            
            # OA badge
            oa_badge = '<span class="badge badge-oa">🔓 OA</span>' if journal.get('is_oa') else '<span class="badge badge-sub">🔒 Subscription</span>'
            
            # Quartile badge
            quartile = journal.get('quartile', 'N/A')
            if quartile == 'Q1':
                q_badge = '<span class="badge badge-q1">Q1</span>'
            elif quartile == 'Q2':
                q_badge = '<span class="badge badge-q2">Q2</span>'
            elif quartile == 'Q3':
                q_badge = '<span class="badge badge-q3">Q3</span>'
            elif quartile == 'Q4':
                q_badge = '<span class="badge badge-q4">Q4</span>'
            else:
                q_badge = '<span class="badge badge-na">N/A</span>'
            
            # IF display
            if_value = journal.get('impact_factor', 0)
            if_display = f"{if_value:.1f}" if if_value > 0 else 'N/A'
            
            # Countries
            countries = journal.get('countries', [])
            countries_display = ', '.join(countries[:5]) if countries else 'N/A'
            if len(countries) > 5:
                countries_display += f' +{len(countries)-5} more'
            
            # Topics
            topics = journal.get('topics', [])
            topics_display = ', '.join(topics[:3]) if topics else 'N/A'
            
            # Domains, Fields, Subfields
            domains = journal.get('domains', [])
            domains_display = ', '.join(domains[:2]) if domains else 'N/A'
            fields = journal.get('fields', [])
            fields_display = ', '.join(fields[:2]) if fields else 'N/A'
            subfields = journal.get('subfields', [])
            subfields_display = ', '.join(subfields[:2]) if subfields else 'N/A'
            
            # SDG
            sdg = journal.get('sdg', [])
            sdg_display = ', '.join(sdg[:3]) if sdg else 'N/A'
            
            # Homepage
            homepage = journal.get('homepage_url', '')
            homepage_link = f'<a href="{homepage}" target="_blank" class="clickable-link">{self.t("visit")}</a>' if homepage else 'N/A'
            
            cards += f"""
            <div class="journal-card">
                <div class="journal-header">
                    <span class="journal-rank">#{i}</span>
                    <span class="journal-name">{journal.get('name', 'Unknown')}</span>
                    <span class="journal-score {score_class}">{score_pct}</span>
                </div>
                <div class="journal-metrics">
                    <div class="metric">
                        <span class="metric-label">{self.t('papers')}</span>
                        <span class="metric-value">{journal.get('works_count', 0)}</span>
                    </div>
                    <div class="metric">
                        <span class="metric-label">{self.t('relevance')}</span>
                        <span class="metric-value">{journal.get('relevance_score', 0):.2f}</span>
                    </div>
                    <div class="metric">
                        <span class="metric-label">{self.t('impact_factor')}</span>
                        <span class="metric-value">{if_display} {q_badge}</span>
                    </div>
                    <div class="metric">
                        <span class="metric-label">{self.t('h_index')}</span>
                        <span class="metric-value">{journal.get('h_index', 0)}</span>
                    </div>
                </div>
                <div class="journal-details">
                    <div class="detail">
                        <span class="detail-label">🏛️ {self.t('publisher')}:</span>
                        <span class="detail-value">{journal.get('publisher', 'Unknown')}</span>
                        {stm_badge}
                        {oa_badge}
                    </div>
                    <div class="detail">
                        <span class="detail-label">🌍 {self.t('countries')}:</span>
                        <span class="detail-value">{countries_display}</span>
                    </div>
                    <div class="detail">
                        <span class="detail-label">📚 {self.t('html_domain')}:</span>
                        <span class="detail-value">{domains_display}</span>
                    </div>
                    <div class="detail">
                        <span class="detail-label">📚 {self.t('html_field')}:</span>
                        <span class="detail-value">{fields_display}</span>
                    </div>
                    <div class="detail">
                        <span class="detail-label">📚 {self.t('html_subfield')}:</span>
                        <span class="detail-value">{subfields_display}</span>
                    </div>
                    <div class="detail">
                        <span class="detail-label">🏷️ {self.t('topics')}:</span>
                        <span class="detail-value">{topics_display}</span>
                    </div>
                    <div class="detail">
                        <span class="detail-label">🎯 {self.t('html_sdg')}:</span>
                        <span class="detail-value">{sdg_display}</span>
                    </div>
                    <div class="detail">
                        <span class="detail-label">🔗 {self.t('homepage')}:</span>
                        <span class="detail-value">{homepage_link}</span>
                    </div>
                    <div class="detail">
                        <span class="detail-label">ISSN:</span>
                        <span class="detail-value">{', '.join(journal.get('issn', [])[:2])}</span>
                    </div>
                </div>
            </div>
            """
        
        return cards
    
    def _generate_statistics(self) -> str:
        """Generate HTML for statistics section"""
        stats = self.stats
        html = '<div class="stats-section">'
        html += f'<div class="section-title" style="padding: 0 0 15px 0;">{self.t("html_statistics")}</div>'
        
        # Publisher distribution
        pub_dist = stats.get('publisher_distribution', {})
        if pub_dist:
            html += '<h4 style="margin: 15px 0 8px; color: #2d3436;">📊 ' + self.t('by_publisher') + '</h4>'
            html += '<div class="publisher-grid">'
            total = stats.get('total_filtered', 1)
            for pub, count in sorted(pub_dist.items(), key=lambda x: x[1], reverse=True)[:12]:
                pct = (count / total) * 100
                html += f"""
                <div class="publisher-item">
                    <span class="publisher-name">{pub}</span>
                    <span class="publisher-count">{count} ({pct:.1f}%)</span>
                    <div class="progress-bar"><div class="progress-fill" style="width: {pct}%;"></div></div>
                </div>
                """
            html += '</div>'
        
        # OA distribution
        oa_dist = stats.get('oa_distribution', {})
        if oa_dist:
            html += '<h4 style="margin: 20px 0 8px; color: #2d3436;">🔓 ' + self.t('by_oa_status') + '</h4>'
            html += '<div class="stats-grid-3">'
            for status, count in oa_dist.items():
                pct = (count / stats.get('total_filtered', 1)) * 100
                label = self.t('html_open_access') if status else self.t('html_subscription')
                html += f"""
                <div class="stat-card-small">
                    <div class="num">{count}</div>
                    <div class="label">{label} ({pct:.1f}%)</div>
                </div>
                """
            html += '</div>'
        
        # Quartile distribution
        quartile_dist = stats.get('quartile_distribution', {})
        if quartile_dist:
            html += '<h4 style="margin: 20px 0 8px; color: #2d3436;">📊 ' + self.t('by_quartile') + '</h4>'
            html += '<div class="stats-grid-4">'
            for q in ['Q1', 'Q2', 'Q3', 'Q4']:
                count = quartile_dist.get(q, 0)
                pct = (count / stats.get('total_filtered', 1)) * 100
                html += f"""
                <div class="stat-card-small">
                    <div class="num">{count}</div>
                    <div class="label">{q} ({pct:.1f}%)</div>
                </div>
                """
            html += '</div>'
        
        # STM distribution
        stm_stats = stats.get('stm_distribution', {})
        if stm_stats:
            html += '<h4 style="margin: 20px 0 8px; color: #2d3436;">🏛️ ' + self.t('by_stm') + '</h4>'
            html += '<div class="stats-grid-3">'
            total = stats.get('total_filtered', 1)
            stm_count = stm_stats.get('stm', 0)
            non_stm_count = stm_stats.get('non_stm', 0)
            stm_pct = (stm_count / total) * 100 if total > 0 else 0
            non_stm_pct = (non_stm_count / total) * 100 if total > 0 else 0
            html += f"""
            <div class="stat-card-small">
                <div class="num">{stm_count}</div>
                <div class="label">STM ({stm_pct:.1f}%)</div>
            </div>
            <div class="stat-card-small">
                <div class="num">{non_stm_count}</div>
                <div class="label">Non-STM ({non_stm_pct:.1f}%)</div>
            </div>
            """
            html += '</div>'
        
        html += '</div>'
        return html

# ============================================================================
# MAIN APPLICATION
# ============================================================================

def main():
    """Main application function"""
    
    # Initialize session state
    if 'language' not in st.session_state:
        st.session_state['language'] = 'en'
    if 'jcr_data' not in st.session_state:
        st.session_state['jcr_data'] = None
    if 'results' not in st.session_state:
        st.session_state['results'] = None
    if 'analyzed' not in st.session_state:
        st.session_state['analyzed'] = False
    if 'journal_analyzer' not in st.session_state:
        st.session_state['journal_analyzer'] = None
    
    # Language selector
    col_lang1, col_lang2 = st.columns([1, 10])
    with col_lang1:
        lang = st.selectbox(
            "🌐 Language",
            options=['English', 'Русский'],
            index=0 if st.session_state['language'] == 'en' else 1
        )
        st.session_state['language'] = 'en' if lang == 'English' else 'ru'
    
    # Header
    st.markdown(f"# {get_text('app_title')}")
    st.markdown(f"### {get_text('app_subtitle')}")
    st.markdown("---")
    
    # Load JCR data
    with st.spinner(get_text('loading_jcr')):
        if st.session_state['jcr_data'] is None:
            st.session_state['jcr_data'] = load_jcr_data()
            if st.session_state['jcr_data']:
                st.success(get_text('jcr_loaded').format(count=len(st.session_state['jcr_data'])))
            else:
                st.warning(get_text('jcr_not_found'))
    
    # Input section
    with st.container():
        col1, col2 = st.columns(2)
        
        with col1:
            level1 = st.text_input(
                get_text('level1_label'),
                placeholder=get_text('level1_placeholder'),
                key='level1_input'
            )
        
        with col2:
            level2 = st.text_input(
                get_text('level2_label'),
                placeholder=get_text('level2_placeholder'),
                key='level2_input'
            )
    
    # Advanced settings
    with st.expander("⚙️ Advanced Settings", expanded=True):
        # Fixed years info
        st.info(get_text('years_info').format(
            start=DEFAULT_YEARS[0],
            end=DEFAULT_YEARS[-1]
        ))
        
        col3, col4 = st.columns(2)
        
        with col3:
            min_papers = st.number_input(
                get_text('min_papers_label'),
                min_value=1,
                max_value=20,
                value=3,
                help=get_text('min_papers_help')
            )
        
        with col4:
            max_results = st.number_input(
                get_text('max_results_label'),
                min_value=5,
                max_value=50,
                value=20,
                help=get_text('max_results_help')
            )
        
        st.markdown("---")
        
        # Filter: Quartile (checkboxes)
        st.markdown(f"**{get_text('filter_by_quartile')}**")
        col_q1, col_q2, col_q3, col_q4 = st.columns(4)
        with col_q1:
            q1_selected = st.checkbox("Q1", value=True, key="q1_filter")
        with col_q2:
            q2_selected = st.checkbox("Q2", value=True, key="q2_filter")
        with col_q3:
            q3_selected = st.checkbox("Q3", value=True, key="q3_filter")
        with col_q4:
            q4_selected = st.checkbox("Q4", value=True, key="q4_filter")
        
        selected_quartiles = []
        if q1_selected: selected_quartiles.append('Q1')
        if q2_selected: selected_quartiles.append('Q2')
        if q3_selected: selected_quartiles.append('Q3')
        if q4_selected: selected_quartiles.append('Q4')
        
        st.markdown("---")
        
        # Filter: STM (radio)
        st.markdown(f"**{get_text('filter_by_stm')}**")
        stm_filter = st.radio(
            "",
            options=['all', 'stm_only', 'non_stm'],
            format_func=lambda x: {
                'all': get_text('stm_all'),
                'stm_only': get_text('stm_only'),
                'non_stm': get_text('stm_exclude')
            }[x],
            horizontal=True,
            key="stm_filter"
        )
        
        st.markdown("---")
        
        # Filter: Country (selectbox - will be populated after analysis)
        st.markdown(f"**{get_text('filter_by_country')}**")
        country_options = ['All']
        if st.session_state['analyzed'] and st.session_state['journal_analyzer']:
            country_options.extend(st.session_state['journal_analyzer'].get_available_countries())
        country_filter = st.selectbox(
            "",
            options=country_options,
            key="country_filter"
        )
        
        st.markdown("---")
        
        # Filter: SDG (selectbox)
        st.markdown(f"**{get_text('filter_by_sdg')}**")
        sdg_options = ['All'] + list(SDG_LIST.values())
        sdg_filter = st.selectbox(
            "",
            options=sdg_options,
            key="sdg_filter"
        )
    
    # Analyze button
    if st.button(get_text('analyze_btn'), type="primary", use_container_width=True):
        if not level1:
            st.error(get_text('error_no_level1'))
        else:
            with st.spinner(get_text('analyzing')):
                try:
                    # Use fixed years
                    years = DEFAULT_YEARS
                    
                    # Search works
                    works = search_works(level1, level2, years, limit=500)
                    
                    if not works:
                        st.error(get_text('error_no_results'))
                    else:
                        # Analyze journals using the analyzer class
                        analyzer = JournalAnalyzer(works, min_papers)
                        st.session_state['journal_analyzer'] = analyzer
                        
                        journal_data = analyzer.get_journals()
                        
                        if not journal_data:
                            st.error(get_text('error_no_results'))
                        else:
                            # Apply filters
                            filtered_data = analyzer.filter_by_quartile(selected_quartiles)
                            filtered_data = analyzer.filter_by_stm(stm_filter)
                            
                            # Country filter (if selected)
                            if country_filter != 'All':
                                filtered_data = analyzer.filter_by_country(country_filter)
                            
                            # SDG filter (if selected)
                            if sdg_filter != 'All':
                                filtered_data = analyzer.filter_by_sdg(sdg_filter)
                            
                            # Calculate composite scores and prepare for display
                            journals_list = []
                            for source_id, data in filtered_data.items():
                                data['composite_score'] = calculate_composite_score(data)
                                journals_list.append(data)
                            
                            # Sort by composite score
                            journals_list.sort(key=lambda x: x['composite_score'], reverse=True)
                            
                            # Take top N
                            top_journals = journals_list[:max_results]
                            
                            # Prepare stats
                            all_journals = list(journal_data.values())
                            total_found = len(journal_data)
                            total_filtered = len(filtered_data)
                            
                            stats = {
                                'total_found': total_found,
                                'total_filtered': total_filtered,
                                'oa_count': sum(1 for j in filtered_data.values() if j.get('is_oa')),
                                'stm_count': sum(1 for j in filtered_data.values() if j.get('publisher_class', {}).get('is_stm', False)),
                                'publisher_distribution': Counter([j.get('publisher_class', {}).get('group', 'Unknown') for j in filtered_data.values()]),
                                'oa_distribution': {True: sum(1 for j in filtered_data.values() if j.get('is_oa')), False: sum(1 for j in filtered_data.values() if not j.get('is_oa'))},
                                'quartile_distribution': Counter([j.get('quartile', 'N/A') for j in filtered_data.values()]),
                                'stm_distribution': {
                                    'stm': sum(1 for j in filtered_data.values() if j.get('publisher_class', {}).get('is_stm', False)),
                                    'non_stm': sum(1 for j in filtered_data.values() if not j.get('publisher_class', {}).get('is_stm', False))
                                }
                            }
                            
                            # Store results
                            st.session_state['results'] = {
                                'journals': top_journals,
                                'query_info': {
                                    'level1': level1,
                                    'level2': level2,
                                    'years': years
                                },
                                'stats': stats,
                                'all_journals': list(filtered_data.values())
                            }
                            st.session_state['analyzed'] = True
                            
                            st.rerun()
                            
                except Exception as e:
                    st.error(f"Error: {str(e)}")
                    logger.error(f"Analysis error: {e}", exc_info=True)
    
    # Display results
    if st.session_state['analyzed'] and st.session_state['results']:
        results = st.session_state['results']
        journals = results['journals']
        stats = results['stats']
        query_info = results['query_info']
        
        st.markdown("---")
        
        # Stats row
        col_a, col_b, col_c, col_d = st.columns(4)
        with col_a:
            st.metric(get_text('total_journals'), stats['total_found'])
        with col_b:
            st.metric(get_text('after_filtering'), stats['total_filtered'])
        with col_c:
            st.metric(get_text('oa_journals'), stats['oa_count'])
        with col_d:
            st.metric(get_text('stm_journals'), stats['stm_count'])
        
        # Display journals as cards
        st.markdown(f"### {get_text('html_recommendations').format(count=len(journals))}")
        
        for i, journal in enumerate(journals, 1):
            with st.container():
                col1, col2, col3, col4 = st.columns([1, 3, 3, 2])
                
                score = journal.get('composite_score', 0)
                score_pct = f"{score * 100:.1f}%"
                
                # Color for score
                if score >= 0.7:
                    score_color = 'green'
                elif score >= 0.4:
                    score_color = 'orange'
                else:
                    score_color = 'red'
                
                with col1:
                    st.markdown(f"### #{i}")
                    st.markdown(f"**Score:** <span style='color:{score_color};font-size:18px;'>{score_pct}</span>", unsafe_allow_html=True)
                
                with col2:
                    st.markdown(f"**{journal.get('name', 'Unknown')}**")
                    
                    # Publisher info
                    pub_class = journal.get('publisher_class', {})
                    pub_group = pub_class.get('group', 'Unknown')
                    is_stm = pub_class.get('is_stm', False)
                    st.write(f"🏛️ {get_text('publisher')}: {journal.get('publisher', 'Unknown')}")
                    if is_stm:
                        st.write("✅ STM Member")
                    
                    # OA status
                    oa_text = '🔓 Open Access' if journal.get('is_oa') else '🔒 Subscription'
                    st.write(oa_text)
                    
                    # Quartile
                    quartile = journal.get('quartile', 'N/A')
                    st.write(f"📊 {get_text('quartile')}: {quartile}")
                
                with col3:
                    # Metrics
                    if_value = journal.get('impact_factor', 0)
                    if_display = f"{if_value:.1f}" if if_value > 0 else 'N/A'
                    st.write(f"📄 {get_text('papers')}: {journal.get('works_count', 0)}")
                    st.write(f"📈 {get_text('impact_factor')}: {if_display}")
                    st.write(f"🔗 {get_text('h_index')}: {journal.get('h_index', 0)}")
                    st.write(f"📊 {get_text('relevance')}: {journal.get('relevance_score', 0):.2f}")
                
                with col4:
                    # Additional info
                    countries = journal.get('countries', [])
                    st.write(f"🌍 {get_text('countries')}: {', '.join(countries[:3]) if countries else 'N/A'}")
                    
                    # Topics
                    topics = journal.get('topics', [])
                    if topics:
                        st.write(f"🏷️ {get_text('topics')}: {', '.join(topics[:3])}")
                    
                    # Domains
                    domains = journal.get('domains', [])
                    if domains:
                        st.write(f"📚 Domain: {', '.join(domains[:2])}")
                    
                    # SDG
                    sdg = journal.get('sdg', [])
                    if sdg:
                        st.write(f"🎯 SDG: {', '.join(sdg[:2])}")
                    
                    homepage = journal.get('homepage_url', '')
                    if homepage:
                        st.markdown(f"🔗 [{get_text('visit')}]({homepage})")
                    
                    issn = journal.get('issn', [])
                    if issn:
                        st.write(f"ISSN: {', '.join(issn[:2])}")
                
                st.markdown("---")
        
        # Export buttons
        col_export1, col_export2 = st.columns(2)
        
        with col_export1:
            # Export HTML
            if st.button("📄 Export HTML Report", use_container_width=True):
                report_gen = ReportGenerator(
                    journals,
                    query_info,
                    stats,
                    st.session_state['language']
                )
                html_report = report_gen.generate()
                
                st.download_button(
                    label="📥 Download HTML Report",
                    data=html_report,
                    file_name=f"journal_recommendation_{datetime.now().strftime('%Y%m%d_%H%M%S')}.html",
                    mime="text/html",
                    use_container_width=True
                )
        
        with col_export2:
            # Export CSV
            if st.button("📊 Export CSV", use_container_width=True):
                csv_data = []
                for journal in journals:
                    csv_data.append({
                        'Rank': journals.index(journal) + 1,
                        'Journal': journal.get('name', ''),
                        'Publisher': journal.get('publisher', ''),
                        'Publisher Type': journal.get('publisher_class', {}).get('category', ''),
                        'STM Member': journal.get('publisher_class', {}).get('is_stm', False),
                        'Open Access': journal.get('is_oa', False),
                        'Papers': journal.get('works_count', 0),
                        'Relevance Score': f"{journal.get('relevance_score', 0):.3f}",
                        'Composite Score': f"{journal.get('composite_score', 0):.3f}",
                        'Impact Factor': journal.get('impact_factor', 0),
                        'Quartile': journal.get('quartile', 'N/A'),
                        'h-index': journal.get('h_index', 0),
                        'Countries': ', '.join(journal.get('countries', [])),
                        'Domains': ', '.join(journal.get('domains', [])),
                        'Fields': ', '.join(journal.get('fields', [])),
                        'Subfields': ', '.join(journal.get('subfields', [])),
                        'Topics': ', '.join(journal.get('topics', [])),
                        'SDG': ', '.join(journal.get('sdg', [])),
                        'ISSN': ', '.join(journal.get('issn', [])),
                        'Homepage': journal.get('homepage_url', '')
                    })
                
                df = pd.DataFrame(csv_data)
                csv = df.to_csv(index=False).encode('utf-8-sig')
                
                st.download_button(
                    label="📥 Download CSV",
                    data=csv,
                    file_name=f"journal_recommendation_{datetime.now().strftime('%Y%m%d_%H%M%S')}.csv",
                    mime="text/csv",
                    use_container_width=True
                )

if __name__ == "__main__":
    main()
