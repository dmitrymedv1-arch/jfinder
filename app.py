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
        'years_label': '📅 Publication Years',
        'years_help': 'Select the time period for analysis',
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
        'citation_impact': 'Citation Impact',
        'countries': 'Countries',
        'topics': 'Topics',
        'homepage': 'Homepage',
        'issn': 'ISSN',
        'visit': 'Visit',
        'score': 'Score',
        'filter_by_country': '🌍 Filter by Country',
        'filter_by_topic': '🏷️ Filter by Topic',
        'topic_level': 'Topic Level',
        'all_countries': 'All Countries',
        'all_topics': 'All Topics',
        'statistics': '📊 Statistics',
        'by_publisher': 'By Publisher',
        'by_oa_status': 'By OA Status',
        'by_quartile': 'By Quartile',
        'top_publishers': 'Top Publishers',
        'stm_members': 'STM Members',
        'university_presses': 'University Presses',
        'scientific_societies': 'Scientific Societies',
        'oa_publishers': 'OA Specialists',
        'other_publishers': 'Other',
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
        'html_copyright': '© 2026 Journal Recommender Tool'
    },
    'ru': {
        'app_title': '📚 Рекомендатель журналов',
        'app_subtitle': 'Найдите наиболее релевантные журналы для вашего исследования',
        'level1_label': 'Уровень 1 (Основная область)',
        'level1_placeholder': 'например, "водородная энергетика", "искусственный интеллект"',
        'level2_label': 'Уровень 2 (Уточнение - опционально)',
        'level2_placeholder': 'например, "высокоэнтропийные оксиды", "глубокое обучение"',
        'years_label': '📅 Годы публикаций',
        'years_help': 'Выберите временной период для анализа',
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
        'citation_impact': 'Цитируемость',
        'countries': 'Страны',
        'topics': 'Темы',
        'homepage': 'Сайт',
        'issn': 'ISSN',
        'visit': 'Перейти',
        'score': 'Балл',
        'filter_by_country': '🌍 Фильтр по стране',
        'filter_by_topic': '🏷️ Фильтр по теме',
        'topic_level': 'Уровень темы',
        'all_countries': 'Все страны',
        'all_topics': 'Все темы',
        'statistics': '📊 Статистика',
        'by_publisher': 'По издателям',
        'by_oa_status': 'По типу доступа',
        'by_quartile': 'По квартилям',
        'top_publishers': 'Топ издателей',
        'stm_members': 'Члены STM',
        'university_presses': 'Университетские издательства',
        'scientific_societies': 'Научные общества',
        'oa_publishers': 'OA специалисты',
        'other_publishers': 'Другие',
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
        'html_copyright': '© 2026 Инструмент рекомендации журналов'
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
    
    best_if = 0.0
    best_quartile = 'N/A'
    
    for issn in issns:
        if issn and issn in jcr_data:
            data = jcr_data[issn]
            if data['if'] > best_if:
                best_if = data['if']
            if quartile_is_better(data['quartile'], best_quartile):
                best_quartile = data['quartile']
    
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
    
    # Extract ISSNs
    issns = []
    if source:
        issn_list = source.get('issn', [])
        if isinstance(issn_list, list):
            issns = issn_list
        elif isinstance(issn_list, str):
            issns = [issn_list]
    
    # Extract concepts
    concepts = []
    for concept in work.get('concepts', [])[:5]:
        if concept.get('display_name'):
            concepts.append({
                'name': concept['display_name'],
                'score': concept.get('score', 0)
            })
    
    return {
        'id': work.get('id', ''),
        'title': clean_text(work.get('title', '')),
        'publication_year': work.get('publication_year', 0),
        'cited_by_count': work.get('cited_by_count', 0),
        'relevance_score': work.get('relevance_score', 0),
        'doi': work.get('doi', '').replace('https://doi.org/', ''),
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

def analyze_journals(works: List[Dict], min_papers: int = 3) -> Dict:
    """Analyze journals from works data"""
    # Group works by source
    source_works = defaultdict(list)
    for work in works:
        enriched = enrich_work_data(work)
        source_id = enriched.get('source_id', '')
        if source_id:
            source_works[source_id].append(enriched)
    
    # Analyze each source
    journal_data = {}
    
    for source_id, works_list in source_works.items():
        if len(works_list) < min_papers:
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
        
        # Concepts
        all_concepts = Counter()
        for w in works_list:
            for concept in w.get('concepts', []):
                all_concepts[concept['name']] += 1
        
        # Get ISSNs
        issns = source_meta.get('issn', [])
        if not issns:
            # Try to get from works
            for w in works_list:
                if w.get('source_issn'):
                    issns = w['source_issn']
                    break
        
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
        
        journal_data[source_id] = {
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
            'works': works_list,
            'impact_factor': jcr_metrics.get('if', 0),
            'quartile': jcr_metrics.get('quartile', 'N/A')
        }
    
    return journal_data

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

def get_author_countries(works: List[Dict]) -> List[str]:
    """Get unique countries from works"""
    countries = set()
    for work in works:
        countries.update(work.get('countries', []))
    return sorted(list(countries))

def get_journal_topics(journal: Dict) -> List[str]:
    """Get topics from journal data"""
    topics = []
    if journal.get('top_concepts'):
        topics = [c[0] for c in journal['top_concepts'][:5]]
    
    # Also get topics from source metadata
    # This is a simplification - in real use, we'd query the source endpoint
    
    return topics

# ============================================================================
# HTML REPORT GENERATOR
# ============================================================================

def generate_html_report(journals: List[Dict], query_info: Dict, stats: Dict, lang: str = 'en') -> str:
    """Generate HTML report with journal recommendations"""
    
    def t(key: str) -> str:
        if lang == 'ru' and key in TEXTS['ru']:
            return TEXTS['ru'][key]
        return TEXTS['en'].get(key, key)
    
    # Get colors based on language
    primary_color = '#667eea'
    secondary_color = '#f39c12'
    
    # Helper for clickable links
    def make_clickable_link(url: str, text: str) -> str:
        if url and url != 'N/A':
            return f'<a href="{url}" target="_blank" class="clickable-link">{text}</a>'
        return text
    
    # Generate journal cards
    journal_cards = ""
    for i, journal in enumerate(journals[:20], 1):
        score = journal.get('composite_score', 0)
        score_pct = f"{score * 100:.1f}%"
        
        # Color for score
        if score >= 0.8:
            score_color = '#28a745'
        elif score >= 0.6:
            score_color = '#ffc107'
        elif score >= 0.4:
            score_color = '#fd7e14'
        else:
            score_color = '#dc3545'
        
        # Publisher badge
        pub_class = journal.get('publisher_class', {})
        pub_category = pub_class.get('category', 'OTHER')
        pub_group = pub_class.get('group', 'Unknown')
        is_stm = pub_class.get('is_stm', False)
        
        if is_stm:
            pub_badge = f'<span class="badge badge-stm">STM</span>'
        elif pub_category == 'UNIVERSITY_PRESSES':
            pub_badge = f'<span class="badge badge-university">🏛️ University</span>'
        elif pub_category == 'SCIENTIFIC_SOCIETIES':
            pub_badge = f'<span class="badge badge-society">🔬 Society</span>'
        elif pub_category == 'OA_SPECIALISTS':
            pub_badge = f'<span class="badge badge-oa">🌐 OA Specialist</span>'
        else:
            pub_badge = f'<span class="badge badge-other">Other</span>'
        
        # OA badge
        oa_badge = '🔓' if journal.get('is_oa') else '🔒'
        oa_text = 'Open Access' if journal.get('is_oa') else 'Subscription'
        
        # IF display
        if_value = journal.get('impact_factor', 0)
        if_display = f"{if_value:.1f}" if if_value > 0 else 'N/A'
        quartile = journal.get('quartile', 'N/A')
        
        # Countries
        countries = journal.get('countries', [])
        countries_display = ', '.join(countries[:5]) if countries else 'N/A'
        if len(countries) > 5:
            countries_display += f' +{len(countries)-5} more'
        
        # Topics
        topics = journal.get('top_concepts', [])
        topics_display = ', '.join([t[0] for t in topics[:3]]) if topics else 'N/A'
        
        # Homepage
        homepage = journal.get('homepage_url', '')
        homepage_link = make_clickable_link(homepage, t('visit'))
        
        journal_cards += f"""
        <div class="journal-card" style="border-left: 4px solid {score_color};">
            <div class="journal-header">
                <div class="journal-rank">#{i}</div>
                <div class="journal-name">{journal.get('name', 'Unknown')}</div>
                <div class="journal-score" style="color: {score_color};">
                    {score_pct}
                </div>
            </div>
            <div class="journal-metrics">
                <div class="metric">
                    <span class="metric-label">📄 {t('papers')}</span>
                    <span class="metric-value">{journal.get('works_count', 0)}</span>
                </div>
                <div class="metric">
                    <span class="metric-label">📊 {t('relevance')}</span>
                    <span class="metric-value">{journal.get('relevance_score', 0):.2f}</span>
                </div>
                <div class="metric">
                    <span class="metric-label">📈 {t('impact_factor')}</span>
                    <span class="metric-value">{if_display} {quartile}</span>
                </div>
                <div class="metric">
                    <span class="metric-label">🔗 {t('h_index')}</span>
                    <span class="metric-value">{journal.get('h_index', 0)}</span>
                </div>
            </div>
            <div class="journal-details">
                <div class="detail">
                    <span class="detail-label">🏛️ {t('publisher')}:</span>
                    <span class="detail-value">{journal.get('publisher', 'Unknown')}</span>
                    {pub_badge}
                </div>
                <div class="detail">
                    <span class="detail-label">🔓 {t('oa_status')}:</span>
                    <span class="detail-value">{oa_badge} {oa_text}</span>
                </div>
                <div class="detail">
                    <span class="detail-label">🌍 {t('countries')}:</span>
                    <span class="detail-value">{countries_display}</span>
                </div>
                <div class="detail">
                    <span class="detail-label">🏷️ {t('topics')}:</span>
                    <span class="detail-value">{topics_display}</span>
                </div>
                <div class="detail">
                    <span class="detail-label">🔗 {t('homepage')}:</span>
                    <span class="detail-value">{homepage_link}</span>
                </div>
                <div class="detail">
                    <span class="detail-label">ISSN:</span>
                    <span class="detail-value">{', '.join(journal.get('issn', []))}</span>
                </div>
            </div>
        </div>
        """
    
    # Generate statistics
    stats_html = ""
    if stats:
        # Publisher distribution
        pub_dist = stats.get('publisher_distribution', {})
        if pub_dist:
            stats_html += f"""
            <div class="stat-section">
                <h4>{t('by_publisher')}</h4>
                <div class="publisher-grid">
            """
            for pub, count in sorted(pub_dist.items(), key=lambda x: x[1], reverse=True)[:10]:
                pct = (count / stats.get('total_filtered', 1)) * 100
                stats_html += f"""
                <div class="publisher-item">
                    <span class="publisher-name">{pub}</span>
                    <span class="publisher-count">{count} ({pct:.1f}%)</span>
                    <div class="progress-bar"><div class="progress-fill" style="width: {pct}%;"></div></div>
                </div>
                """
            stats_html += """
                </div>
            </div>
            """
        
        # OA distribution
        oa_dist = stats.get('oa_distribution', {})
        if oa_dist:
            stats_html += f"""
            <div class="stat-section">
                <h4>{t('by_oa_status')}</h4>
                <div class="stats-grid-3">
            """
            for status, count in oa_dist.items():
                pct = (count / stats.get('total_filtered', 1)) * 100
                label = 'Open Access' if status else 'Subscription'
                stats_html += f"""
                <div class="stat-card">
                    <div class="stat-number">{count}</div>
                    <div class="stat-percent">{pct:.1f}%</div>
                    <div class="stat-label">{label}</div>
                </div>
                """
            stats_html += """
            </div>
            """
        
        # Quartile distribution
        quartile_dist = stats.get('quartile_distribution', {})
        if quartile_dist:
            stats_html += f"""
            <div class="stat-section">
                <h4>{t('by_quartile')}</h4>
                <div class="stats-grid-4">
            """
            for q in ['Q1', 'Q2', 'Q3', 'Q4']:
                count = quartile_dist.get(q, 0)
                pct = (count / stats.get('total_filtered', 1)) * 100
                stats_html += f"""
                <div class="stat-card">
                    <div class="stat-number">{count}</div>
                    <div class="stat-percent">{pct:.1f}%</div>
                    <div class="stat-label">{q}</div>
                </div>
                """
            stats_html += """
            </div>
            """
    
    # Build full HTML
    html = f"""<!DOCTYPE html>
<html lang="{lang}">
<head>
    <meta charset="UTF-8">
    <meta name="viewport" content="width=device-width, initial-scale=1.0">
    <title>{t('html_report_title')}</title>
    <style>
        * {{ margin: 0; padding: 0; box-sizing: border-box; }}
        body {{
            font-family: 'Segoe UI', Tahoma, Geneva, Verdana, sans-serif;
            background: #f5f7fa;
            padding: 20px;
        }}
        .container {{
            max-width: 1400px;
            margin: 0 auto;
            background: white;
            border-radius: 15px;
            padding: 30px;
            box-shadow: 0 10px 40px rgba(0,0,0,0.1);
        }}
        .header {{
            background: linear-gradient(135deg, {primary_color} 0%, {secondary_color} 100%);
            color: white;
            padding: 30px;
            border-radius: 12px;
            margin-bottom: 30px;
        }}
        .header h1 {{ font-size: 28px; margin-bottom: 10px; }}
        .header .meta {{ opacity: 0.9; font-size: 14px; }}
        .stats-grid {{
            display: grid;
            grid-template-columns: repeat(auto-fit, minmax(180px, 1fr));
            gap: 15px;
            margin-bottom: 30px;
        }}
        .stats-grid-3 {{
            display: grid;
            grid-template-columns: repeat(3, 1fr);
            gap: 15px;
            margin-bottom: 20px;
        }}
        .stats-grid-4 {{
            display: grid;
            grid-template-columns: repeat(4, 1fr);
            gap: 15px;
            margin-bottom: 20px;
        }}
        .stat-card {{
            background: #f8f9fa;
            border-radius: 10px;
            padding: 15px;
            text-align: center;
        }}
        .stat-number {{
            font-size: 28px;
            font-weight: bold;
            color: {primary_color};
        }}
        .stat-percent {{
            font-size: 14px;
            color: #666;
        }}
        .stat-label {{
            font-size: 12px;
            color: #888;
            margin-top: 5px;
        }}
        .journal-card {{
            background: #f8f9fa;
            border-radius: 10px;
            padding: 20px;
            margin-bottom: 15px;
            transition: transform 0.2s;
            border-left: 4px solid #667eea;
        }}
        .journal-card:hover {{
            transform: translateX(5px);
            background: #f0f2f5;
        }}
        .journal-header {{
            display: flex;
            align-items: center;
            justify-content: space-between;
            margin-bottom: 12px;
        }}
        .journal-rank {{
            font-size: 18px;
            font-weight: bold;
            color: {primary_color};
            background: white;
            padding: 4px 12px;
            border-radius: 20px;
        }}
        .journal-name {{
            font-size: 18px;
            font-weight: 600;
            flex: 1;
            margin-left: 15px;
        }}
        .journal-score {{
            font-size: 20px;
            font-weight: bold;
            padding: 4px 12px;
            border-radius: 20px;
            background: white;
        }}
        .journal-metrics {{
            display: grid;
            grid-template-columns: repeat(auto-fit, minmax(120px, 1fr));
            gap: 10px;
            margin-bottom: 12px;
        }}
        .metric {{
            background: white;
            padding: 8px 12px;
            border-radius: 8px;
            display: flex;
            justify-content: space-between;
            align-items: center;
        }}
        .metric-label {{
            font-size: 12px;
            color: #888;
        }}
        .metric-value {{
            font-weight: 600;
            color: #333;
        }}
        .journal-details {{
            display: grid;
            grid-template-columns: 1fr 1fr;
            gap: 8px 20px;
            font-size: 13px;
        }}
        .detail {{
            display: flex;
            align-items: center;
            gap: 5px;
        }}
        .detail-label {{
            color: #888;
            font-weight: 500;
        }}
        .detail-value {{
            color: #333;
        }}
        .badge {{
            display: inline-block;
            padding: 2px 10px;
            border-radius: 12px;
            font-size: 11px;
            font-weight: 600;
            margin-left: 5px;
        }}
        .badge-stm {{ background: #e3f2fd; color: #1565c0; }}
        .badge-university {{ background: #f3e5f5; color: #6a1b9a; }}
        .badge-society {{ background: #e8f5e9; color: #2e7d32; }}
        .badge-oa {{ background: #fff3e0; color: #e65100; }}
        .badge-other {{ background: #eceff1; color: #546e7a; }}
        .clickable-link {{
            color: {primary_color};
            text-decoration: none;
        }}
        .clickable-link:hover {{
            text-decoration: underline;
        }}
        .stat-section {{
            margin-top: 20px;
            padding-top: 20px;
            border-top: 1px solid #e0e0e0;
        }}
        .stat-section h4 {{
            margin-bottom: 12px;
            color: #333;
        }}
        .publisher-grid {{
            display: grid;
            grid-template-columns: 1fr 1fr;
            gap: 8px;
        }}
        .publisher-item {{
            display: flex;
            align-items: center;
            gap: 10px;
            font-size: 13px;
        }}
        .publisher-name {{
            min-width: 150px;
            color: #333;
        }}
        .publisher-count {{
            min-width: 60px;
            color: #666;
            font-size: 12px;
        }}
        .progress-bar {{
            flex: 1;
            height: 6px;
            background: #e0e0e0;
            border-radius: 3px;
            overflow: hidden;
        }}
        .progress-fill {{
            height: 100%;
            background: linear-gradient(90deg, {primary_color}, {secondary_color});
            border-radius: 3px;
        }}
        .footer {{
            text-align: center;
            padding: 20px;
            color: #888;
            font-size: 12px;
            margin-top: 30px;
            border-top: 1px solid #e0e0e0;
        }}
        @media (max-width: 768px) {{
            .journal-details {{ grid-template-columns: 1fr; }}
            .publisher-grid {{ grid-template-columns: 1fr; }}
            .stats-grid-3, .stats-grid-4 {{ grid-template-columns: 1fr 1fr; }}
        }}
        @media print {{
            body {{ background: white; padding: 0; }}
            .container {{ box-shadow: none; padding: 20px; }}
        }}
    </style>
</head>
<body>
    <div class="container">
        <div class="header">
            <h1>{t('html_report_title')}</h1>
            <div class="meta">
                <div><strong>{t('query')}:</strong> {query_info.get('level1', '')}{' + ' + query_info.get('level2', '') if query_info.get('level2') else ''}</div>
                <div><strong>{t('period')}:</strong> {query_info.get('years', [])}</div>
                <div><strong>{t('generated')}:</strong> {datetime.now().strftime('%Y-%m-%d %H:%M')}</div>
            </div>
        </div>
        
        <div class="stats-grid">
            <div class="stat-card">
                <div class="stat-number">{stats.get('total_found', 0)}</div>
                <div class="stat-label">{t('html_total_journals')}</div>
            </div>
            <div class="stat-card">
                <div class="stat-number">{stats.get('total_filtered', 0)}</div>
                <div class="stat-label">{t('html_after_filtering')}</div>
            </div>
            <div class="stat-card">
                <div class="stat-number">{stats.get('oa_count', 0)}</div>
                <div class="stat-label">{t('html_oa_journals')}</div>
            </div>
            <div class="stat-card">
                <div class="stat-number">{stats.get('stm_count', 0)}</div>
                <div class="stat-label">{t('html_stm_journals')}</div>
            </div>
        </div>
        
        {stats_html}
        
        <h2 style="margin: 25px 0 15px 0;">{t('html_recommendations').format(count=min(len(journals), 20))}</h2>
        
        {journal_cards}
        
        <div class="footer">
            {t('html_footer')}<br>
            {t('html_copyright')}
        </div>
    </div>
</body>
</html>"""
    
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
    with st.expander("⚙️ Advanced Settings"):
        col3, col4, col5 = st.columns(3)
        
        with col3:
            current_year = datetime.now().year
            year_range = st.slider(
                get_text('years_label'),
                min_value=2000,
                max_value=current_year,
                value=(current_year - 2, current_year),
                help=get_text('years_help')
            )
            years = list(range(year_range[0], year_range[1] + 1))
        
        with col4:
            min_papers = st.number_input(
                get_text('min_papers_label'),
                min_value=1,
                max_value=20,
                value=3,
                help=get_text('min_papers_help')
            )
        
        with col5:
            max_results = st.number_input(
                get_text('max_results_label'),
                min_value=5,
                max_value=50,
                value=20,
                help=get_text('max_results_help')
            )
        
        # Filters
        col6, col7 = st.columns(2)
        
        with col6:
            # Country filter (will be populated after analysis)
            st.markdown(f"**{get_text('filter_by_country')}**")
            country_filter = st.text_input(
                "Country code (e.g., US, CN, GB)",
                placeholder="Leave empty for all",
                key='country_filter'
            )
        
        with col7:
            # Topic filter (will be populated after analysis)
            st.markdown(f"**{get_text('filter_by_topic')}**")
            topic_filter = st.text_input(
                "Topic keyword",
                placeholder="Leave empty for all",
                key='topic_filter'
            )
    
    # Analyze button
    if st.button(get_text('analyze_btn'), type="primary", use_container_width=True):
        if not level1:
            st.error(get_text('error_no_level1'))
        else:
            with st.spinner(get_text('analyzing')):
                try:
                    # Search works
                    works = search_works(level1, level2, years, limit=500)
                    
                    if not works:
                        st.error(get_text('error_no_results'))
                    else:
                        # Analyze journals
                        journal_data = analyze_journals(works, min_papers)
                        
                        if not journal_data:
                            st.error(get_text('error_no_results'))
                        else:
                            # Calculate composite scores and prepare for display
                            journals_list = []
                            for source_id, data in journal_data.items():
                                data['composite_score'] = calculate_composite_score(data)
                                journals_list.append(data)
                            
                            # Sort by composite score
                            journals_list.sort(key=lambda x: x['composite_score'], reverse=True)
                            
                            # Apply filters
                            filtered_journals = journals_list
                            
                            if country_filter:
                                country_filter_upper = country_filter.upper()
                                filtered_journals = [
                                    j for j in filtered_journals
                                    if any(c.upper() == country_filter_upper for c in j.get('countries', []))
                                ]
                            
                            if topic_filter:
                                topic_filter_lower = topic_filter.lower()
                                filtered_journals = [
                                    j for j in filtered_journals
                                    if any(topic_filter_lower in c[0].lower() for c in j.get('top_concepts', []))
                                ]
                            
                            # Take top N
                            top_journals = filtered_journals[:max_results]
                            
                            # Prepare stats
                            stats = {
                                'total_found': len(journal_data),
                                'total_filtered': len(filtered_journals),
                                'oa_count': sum(1 for j in filtered_journals if j.get('is_oa')),
                                'stm_count': sum(1 for j in filtered_journals if j.get('publisher_class', {}).get('is_stm', False)),
                                'publisher_distribution': Counter([j.get('publisher_class', {}).get('group', 'Unknown') for j in filtered_journals]),
                                'oa_distribution': {True: sum(1 for j in filtered_journals if j.get('is_oa')), False: sum(1 for j in filtered_journals if not j.get('is_oa'))},
                                'quartile_distribution': Counter([j.get('quartile', 'N/A') for j in filtered_journals])
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
                                'all_journals': filtered_journals
                            }
                            st.session_state['analyzed'] = True
                            
                            st.rerun()
                            
                except Exception as e:
                    st.error(f"Error: {str(e)}")
    
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
                if score >= 0.8:
                    score_color = 'green'
                elif score >= 0.6:
                    score_color = 'orange'
                elif score >= 0.4:
                    score_color = 'darkorange'
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
                
                with col3:
                    # Metrics
                    if_value = journal.get('impact_factor', 0)
                    if_display = f"{if_value:.1f}" if if_value > 0 else 'N/A'
                    st.write(f"📄 {get_text('papers')}: {journal.get('works_count', 0)}")
                    st.write(f"📈 {get_text('impact_factor')}: {if_display} {journal.get('quartile', 'N/A')}")
                    st.write(f"🔗 {get_text('h_index')}: {journal.get('h_index', 0)}")
                    st.write(f"📊 {get_text('relevance')}: {journal.get('relevance_score', 0):.2f}")
                
                with col4:
                    # Additional info
                    countries = journal.get('countries', [])
                    st.write(f"🌍 {get_text('countries')}: {', '.join(countries[:3]) if countries else 'N/A'}")
                    
                    topics = journal.get('top_concepts', [])
                    if topics:
                        st.write(f"🏷️ {get_text('topics')}: {', '.join([t[0] for t in topics[:3]])}")
                    
                    homepage = journal.get('homepage_url', '')
                    if homepage:
                        st.markdown(f"🔗 [{get_text('visit')}]({homepage})")
                    
                    issn = journal.get('issn', [])
                    if issn:
                        st.write(f"ISSN: {', '.join(issn[:2])}")
                
                st.markdown("---")
        
        # Export HTML
        if st.button("📄 Export HTML Report", use_container_width=True):
            html_report = generate_html_report(
                journals,
                query_info,
                stats,
                st.session_state['language']
            )
            
            st.download_button(
                label="📥 Download HTML Report",
                data=html_report,
                file_name=f"journal_recommendation_{datetime.now().strftime('%Y%m%d_%H%M%S')}.html",
                mime="text/html",
                use_container_width=True
            )
        
        # Export CSV
        if st.button("📊 Export CSV", use_container_width=True):
            # Prepare data for CSV
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
