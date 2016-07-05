from django.shortcuts import render
from django.shortcuts import render_to_response
from django.http import HttpResponse
from django.template import RequestContext

from django.core.paginator import Paginator, EmptyPage, PageNotAnInteger
from operator import itemgetter, attrgetter

import core.searcher
import core.company
import core.concept

# Create your views here.
def index(request):

    context = {}
    
    return render_to_response('main/index.html', context, context_instance = RequestContext(request))

def helper(request):

    context = {}
    
    return render_to_response('main/help.html', context, context_instance = RequestContext(request))


def search(request):
    ip = get_client_ip(request)
    if request.POST:
        query = request.POST['dcm_query']
    else:
        query = ""
    results = core.searcher.fulltext_search(query, ip)
    context = {
        "query": query 
    }
        
    context['hits'] = results[0]
    context['companies'] = results[1]
    return render_to_response('main/search.html', context, context_instance = RequestContext(request))

def search_keyword(request, keyword):

    results = core.searcher.fulltext_search(keyword)
    context = {
        "query": keyword 
    }
        
    context['hits'] = results[0]
    context['companies'] = results[1]
    return render_to_response('main/search.html', context, context_instance = RequestContext(request))


def search_company(request, company):
    #query = request.POST['dcm_query']
    results = core.company.getCompanyConcepts(company)
    context = {
        "company": company 
    }
        
    context['concepts'] = results
    return render_to_response('main/company.html', context, context_instance = RequestContext(request))

def explore(request):
    results = core.concept.getConcepts()
    companies = core.company.getCompanies()
    context = {}
        
    context['concepts'] = results
    context['companies'] = companies
    return render_to_response('main/explore.html', context, context_instance = RequestContext(request))

def listing(request):
    keyword = request.GET.get('keyword')
    company = request.GET.get('company')
    sortby = request.GET.get('sortby')
    if 'user' in request.GET:
        user = request.GET.get('user')
    else:
        user = ''
    if 'concept' in request.GET:
        concept = request.GET.get('concept')
    else:
        concept = ''
    if 'source' in request.GET:
        source = request.GET.get('source')
    else:
        source = ''
            
    MAX_PUBS = 500
    results = core.searcher.fulltext_search_filter_by_company(keyword, company, user, concept, source, maximum = MAX_PUBS)
    context = {
        "query": keyword ,
        "company": company,
        "sortby" : sortby,
        'concept': concept,
        'user': user,
        'source': source
    }
    
    scholar_list = results[1][0]['publication']
    context['company_name'] = results[1][0]['company_name']
    context['total_pub'] = len(scholar_list)
    context['author_summary'] = results[1][0]['author_summary']
    context['concept_summary'] = results[1][0]['concept_summary']
    
    scholar_list = scholar_list[0:MAX_PUBS-1]
    
    if sortby == 'year':
        scholar_list = sorted(scholar_list, key= itemgetter("year"), reverse=True )
    elif sortby == 'if_score':
        scholar_list = sorted(scholar_list, key= itemgetter("if_score"), reverse=True )

    
    paginator = Paginator(scholar_list, 5) # Show 25 contacts per page

    page = request.GET.get('page')
    try:
        publications = paginator.page(page)
    except PageNotAnInteger:
        # If page is not an integer, deliver first page.
        publications = paginator.page(1)
    except EmptyPage:
        # If page is out of range (e.g. 9999), deliver last page of results.
        publications = paginator.page(paginator.num_pages)

    context['publications'] = publications

    return render_to_response('main/listpub.html',context, context_instance = RequestContext(request))

def get_client_ip(request):
    x_forwarded_for = request.META.get('HTTP_X_FORWARDED_FOR')
    if x_forwarded_for:
        ip = x_forwarded_for.split(',')[-1].strip()
    else:
        ip = request.META.get('REMOTE_ADDR')
    return ip