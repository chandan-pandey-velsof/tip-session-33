from django.http import HttpResponse
from django.conf import settings
import requests
import json

def index(request):
    """Default home view — replaced by the AI agent to implement the requested feature."""
    return HttpResponse(
        "<h1>TIP AI Coder</h1><p>The AI agent will implement your feature here.</p>",
        content_type="text/html",
    )

def tip_api_proxy(request, path):
    """Proxy view for TIP API calls — forwards requests to the real TIP API."""
    url = f"{settings.TIP_API_URL}/{path}"
    headers = {"x-api-key": settings.TIP_API_TOKEN}
    
    try:
        if request.method == "GET":
            response = requests.get(url, headers=headers, params=request.GET)
        elif request.method == "POST":
            response = requests.post(url, headers=headers, json=json.loads(request.body))
        else:
            return HttpResponse("Method not allowed", status=405)
        
        return HttpResponse(response.content, status=response.status_code, content_type="application/json")
    except Exception as e:
        return HttpResponse(f"API error: {str(e)}", status=500)

def examiner_allowance_chart(request):
    """Main page to search an examiner and show allowance vs rejection chart."""
    # Get examiner name from query param
    examiner_name = request.GET.get('examiner', '')
    
    if not examiner_name:
        html = """
        <html>
        <head>
            <link rel='stylesheet' href='/static/tip_design.css'>
        </head>
        <body>
            <div class='tip-page'>
                <h1 class='tip-page-title'>Examiner Allowance Chart</h1>
                <div class='tip-card'>
                    <p>Enter an examiner name to see allowance vs rejection statistics.</p>
                    <form method='get' action=''>
                        <input type='text' name='examiner' placeholder='Examiner Name' value='%s'/>
                        <button type='submit' class='tip-btn tip-btn-primary'>Search</button>
                    </form>
                </div>
            </div>
        </body>
        </html>
        """ % examiner_name
        return HttpResponse(html, content_type="text/html")
    
    # Fetch data from TIP API
    try:
        # Get allowance rate data
        allowance_url = f"{settings.TIP_API_URL}/v1/examiner/allowance-rate"
        headers = {"x-api-key": settings.TIP_API_TOKEN}
        payload = {"examiner_name": examiner_name}
        
        response = requests.post(allowance_url, headers=headers, json=payload)
        data = response.json()
        
        if not data.get("status"):
            error_msg = data.get("message", "Unknown error")
            html = """
            <html>
            <head>
                <link rel='stylesheet' href='/static/tip_design.css'>
            </head>
            <body>
                <div class='tip-page'>
                    <h1 class='tip-page-title'>Examiner Allowance Chart</h1>
                    <div class='tip-card'>
                        <p>Error fetching data: %s</p>
                        <a href='/' class='tip-btn tip-btn-outline'>Back to Search</a>
                    </div>
                </div>
            </body>
            </html>
            """ % error_msg
            return HttpResponse(html, content_type="text/html")
        
        # Extract allowance data
        allowance_data = data["data"]["ex_rule"]["allowance"]
        categories = allowance_data["allowance"]["categories"]
        allowed_series = allowance_data["allowance"]["series"]
        rejected_series = allowance_data["allowance_rej"]["series"]
        
        # Prepare chart data for JavaScript
        chart_data = {
            "categories": categories,
            "allowed": allowed_series,
            "rejected": rejected_series
        }
        
        html = """
        <html>
        <head>
            <link rel='stylesheet' href='/static/tip_design.css'>
            <script src="https://cdn.jsdelivr.net/npm/chart.js"></script>
        </head>
        <body>
            <div class='tip-page'>
                <h1 class='tip-page-title'>Examiner Allowance Chart</h1>
                
                <div class='tip-card'>
                    <p>Allowance vs Rejection for examiner: <strong>%s</strong></p>
                    <canvas id="allowanceChart" width="400" height="200"></canvas>
                </div>
                
                <script>
                    const ctx = document.getElementById('allowanceChart').getContext('2d');
                    const chartData = %s;
                    
                    new Chart(ctx, {
                        type: 'bar',
                        data: {
                            labels: chartData.categories,
                            datasets: [
                                {
                                    label: 'Allowed',
                                    data: chartData.allowed,
                                    backgroundColor: 'rgba(75, 192, 192, 0.2)',
                                    borderColor: 'rgba(75, 192, 192, 1)',
                                    borderWidth: 1
                                },
                                {
                                    label: 'Rejected',
                                    data: chartData.rejected,
                                    backgroundColor: 'rgba(255, 99, 132, 0.2)',
                                    borderColor: 'rgba(255, 99, 132, 1)',
                                    borderWidth: 1
                                }
                            ]
                        },
                        options: {
                            scales: {
                                y: {
                                    beginAtZero: true
                                }
                            }
                        }
                    });
                </script>
                
                <div class='tip-card'>
                    <h2>Diagnostics</h2>
                    <details>
                        <summary>Diagnostics</summary>
                        <p><strong>Request:</strong> %s</p>
                        <p><strong>API call:</strong> POST /v1/examiner/allowance-rate</p>
                        <p><strong>Input parameters:</strong> examiner_name=%s</p>
                        <p><strong>Output parameters:</strong></p>
                        <ul>
                            <li>categories: %s</li>
                            <li>allowed series: %s</li>
                            <li>rejected series: %s</li>
                        </ul>
                        <p><strong>Field mapping:</strong></p>
                        <table class='tip-table'>
                            <tr><td>data.ex_rule.allowance.allowance.categories</td><td>Chart categories</td></tr>
                            <tr><td>data.ex_rule.allowance.allowance.series</td><td>Allowed counts</td></tr>
                            <tr><td>data.ex_rule.allowance.allowance_rej.series</td><td>Rejected counts</td></tr>
                        </table>
                    </details>
                </div>
            </div>
        </body>
        </html>
        """ % (examiner_name, json.dumps(chart_data), request.META.get('QUERY_STRING', ''), examiner_name, 
               ', '.join(categories), ', '.join(map(str, allowed_series)), ', '.join(map(str, rejected_series)))
        
        return HttpResponse(html, content_type="text/html")
        
    except Exception as e:
        html = """
        <html>
        <head>
            <link rel='stylesheet' href='/static/tip_design.css'>
        </head>
        <body>
            <div class='tip-page'>
                <h1 class='tip-page-title'>Examiner Allowance Chart</h1>
                <div class='tip-card'>
                    <p>Error fetching data: %s</p>
                    <a href='/' class='tip-btn tip-btn-outline'>Back to Search</a>
                </div>
            </div>
        </body>
        </html>
        """ % str(e)
        return HttpResponse(html, content_type="text/html")