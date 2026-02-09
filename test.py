import dash
from dash import dcc, html, Input, Output, State, ctx, dash_table
import plotly.graph_objects as go
import plotly.express as px
import pandas as pd
from datetime import datetime, date, timedelta
import webbrowser
from threading import Timer
import re
import uuid

app = dash.Dash(__name__, title="Engineering Schedule Editor")

# --- 1. 現行データ (Initial Data) ---
current_tasks = [
    # --- 商品A ---
    {
        "id": "a01", "section": "商品A", "task": "企画UP", "start": "2023-01-15", "end": "2023-01-15", "next_to": "a02",
        "doc": "商品企画書 Ver.1.0", "action": "企画決裁承認", "lesson": "競合調査に時間を要したため早めの着手が必要"
    },
    {
        "id": "a02", "section": "商品A", "task": "DR0", "start": "2023-01-28", "end": "2023-01-28", "next_to": "a03",
        "doc": "構想設計書, デザン案", "action": "デザイン決定", "lesson": "春節休み前に部品手配を完了させること(先に〇〇手配)"
    },
    {
        "id": "a03", "section": "商品A", "task": "DR1", "start": "2023-02-26", "end": "2023-02-26", "next_to": "a04",
        "doc": "詳細設計書, コスト試算表", "action": "金型手配承認", "lesson": ""
    },
    {
        "id": "a04", "section": "商品A", "task": "DR2", "start": "2023-03-01", "end": "2023-03-01", "next_to": "a05",
        "doc": "試作評価報告書", "action": "ES試作判定", "lesson": "早めに準備を行うこと"
    },
    {
        "id": "a05", "section": "商品A", "task": "AQ0", "start": "2023-03-30", "end": "2023-03-30", "next_to": "a06",
        "doc": "品質保証計画書", "action": "信頼性試験開始", "lesson": ""
    },
    {
        "id": "a06", "section": "商品A", "task": "AQ1", "start": "2023-04-15", "end": "2023-04-15", "next_to": "b04",
        "doc": "CS試作レポート", "action": "量産金型修正指示", "lesson": "商品BのDR2と同日開催回避のため日程調整済み"
    },
    {
        "id": "a07", "section": "商品A", "task": "AQ2", "start": "2023-05-08", "end": "2023-05-08", "next_to": "a08",
        "doc": "最終製品仕様書", "action": "量産移行判定", "lesson": ""
    },
    {
        "id": "a08", "section": "商品A", "task": "発売", "start": "2023-05-15", "end": "2023-05-15", "next_to": "",
        "doc": "プレスリリース", "action": "出荷開始", "lesson": "GW明けの物流混雑に注意"
    },
    # --- 商品B ---
    {
        "id": "b01", "section": "商品B", "task": "企画UP", "start": "2023-02-15", "end": "2023-02-15", "next_to": "b02",
        "doc": "商品企画書 Ver.1.0", "action": "企画決裁承認", "lesson": ""
    },
    {
        "id": "b02", "section": "商品B", "task": "DR0", "start": "2023-02-28", "end": "2023-02-28", "next_to": "b03",
        "doc": "構想設計書", "action": "基本仕様Fix", "lesson": ""
    },
    {
        "id": "b03", "section": "商品B", "task": "DR1", "start": "2023-03-26", "end": "2023-03-26", "next_to": "b04",
        "doc": "詳細設計書", "action": "試作手配", "lesson": ""
    },
    {
        "id": "b04", "section": "商品B", "task": "DR2", "start": "2023-04-01", "end": "2023-04-01", "next_to": "b05",
        "doc": "試作評価報告書", "action": "AQ0判定準備", "lesson": "商品AのAQ1とリソース重複注意"
    },
    {
        "id": "b05", "section": "商品B", "task": "AQ0", "start": "2023-04-28", "end": "2023-04-28", "next_to": "b06",
        "doc": "品質保証計画書", "action": "GW前試験投入", "lesson": "GWを挟むためリードタイム長めに設定"
    },
    {
        "id": "b06", "section": "商品B", "task": "AQ1", "start": "2023-05-15", "end": "2023-05-15", "next_to": "b07",
        "doc": "CS試作レポート", "action": "修正確認", "lesson": "稼働日が少ないため前倒し進行推奨"
    },
    {
        "id": "b07", "section": "商品B", "task": "AQ2", "start": "2023-06-07", "end": "2023-06-07", "next_to": "b08",
        "doc": "最終製品仕様書", "action": "量産可否判定", "lesson": ""
    },
    {
        "id": "b08", "section": "商品B", "task": "発売", "start": "2023-06-30", "end": "2023-06-30", "next_to": "",
        "doc": "販売マニュアル", "action": "店頭導入", "lesson": "上期末の売上計上に間に合わせる"
    }
]

# --- 2. 過去データ (Past Data) ---
past_tasks = [
    {"id": "p01", "section": "過去モデル", "task": "企画UP", "start": "2023-01-01", "end": "2023-01-01", "next_to": "p02", 
     "doc": "企画書", "action": "承認済", "lesson": ""},
    {"id": "p02", "section": "過去モデル", "task": "DR0", "start": "2023-01-08", "end": "2023-01-08", "next_to": "p03", 
     "doc": "構想図", "action": "DR実施", "lesson": ""},
    {"id": "p03", "section": "過去モデル", "task": "決定会議", "start": "2023-01-09", "end": "2023-01-09", "next_to": "p04", 
     "doc": "議事録", "action": "仕様決定", "lesson": "早めに〇〇準備"},
    {"id": "p04", "section": "過去モデル", "task": "DR1", "start": "2023-01-15", "end": "2023-01-15", "next_to": "p05", 
     "doc": "詳細設計書", "action": "出図承認", "lesson": ""},
    {"id": "p05", "section": "過去モデル", "task": "DR2", "start": "2023-01-22", "end": "2023-01-22", "next_to": "p06", 
     "doc": "試作評価書", "action": "判定", "lesson": "先に予定確保"},
    {"id": "p06", "section": "過去モデル", "task": "先行出図", "start": "2023-01-30", "end": "2023-01-30", "next_to": "p07", 
     "doc": "図面一式", "action": "出図", "lesson": "先に行動"},
    {"id": "p07", "section": "過去モデル", "task": "AQ0", "start": "2023-02-03", "end": "2023-02-03", "next_to": "p08", 
     "doc": "品質計画", "action": "試験開始", "lesson": ""},
    {"id": "p08", "section": "過去モデル", "task": "P1", "start": "2023-02-06", "end": "2023-02-10", "next_to": "p09", 
     "doc": "P1レポート", "action": "試作実施", "lesson": "過去トラブルあり"},
    {"id": "p09", "section": "過去モデル", "task": "P2", "start": "2023-02-12", "end": "2023-02-14", "next_to": "p10", 
     "doc": "P2レポート", "action": "試作実施", "lesson": "休日挟み注意"},
    {"id": "p10", "section": "過去モデル", "task": "AQ1", "start": "2023-02-17", "end": "2023-02-17", "next_to": "p11", 
     "doc": "信頼性試験結果", "action": "確認", "lesson": ""},
    {"id": "p11", "section": "過去モデル", "task": "AQ2", "start": "2023-02-21", "end": "2023-02-21", "next_to": "p12", 
     "doc": "最終仕様書", "action": "量産判定", "lesson": ""},
    {"id": "p12", "section": "過去モデル", "task": "発売", "start": "2023-02-28", "end": "2023-02-28", "next_to": "", 
     "doc": "販売計画", "action": "発売開始", "lesson": ""}
]

# コンパクト設定
FONT_S = '13px'
INPUT_H = '24px'

app.layout = html.Div([
    # --- ヘッダー削除 ---
    # html.Div([...]) は削除しました

    # 2. メインコンテンツ (100vh)
    html.Div([
        # === 左カラム: 操作パネル (30%) ===
        html.Div([
            # コンボボックス
            html.Div([
                html.Label("Project", style={'fontWeight': 'bold', 'fontSize': FONT_S}),
                dcc.Dropdown(
                    id='data-selector',
                    options=[{'label': 'Current (商品A/B)', 'value': 'current'}, {'label': 'Past (過去モデル)', 'value': 'past'}],
                    value='current', clearable=False,
                    style={'fontSize': FONT_S, 'height': '30px', 'minHeight': '30px'} # コンパクト化
                )
            ], style={'marginBottom': '10px'}),

            # 入力フォーム
            html.Div([
                html.Div([
                    html.Label("Section", style={'fontSize': FONT_S, 'fontWeight': 'bold'}),
                    dcc.Input(id='input-section', type='text', style={'width': '100%', 'fontSize': FONT_S, 'height': INPUT_H, 'padding': '2px'})
                ], style={'marginBottom': '5px'}),
                
                html.Div([
                    html.Label("Task", style={'fontSize': FONT_S, 'fontWeight': 'bold'}),
                    dcc.Input(id='input-task', type='text', style={'width': '100%', 'fontSize': FONT_S, 'height': INPUT_H, 'padding': '2px'})
                ], style={'marginBottom': '5px'}),

                html.Div([
                    html.Div([html.Label("Start", style={'fontSize': FONT_S}), dcc.Input(id='input-start', type='text', style={'width': '100%', 'fontSize': FONT_S, 'height': INPUT_H})], style={'width': '48%', 'display': 'inline-block'}),
                    html.Div([html.Label("End", style={'fontSize': FONT_S}), dcc.Input(id='input-end', type='text', style={'width': '100%', 'fontSize': FONT_S, 'height': INPUT_H})], style={'width': '48%', 'display': 'inline-block', 'marginLeft': '4%'}),
                ], style={'marginBottom': '5px'}),
                
                html.Div([
                    html.Label("Next ID", style={'fontSize': FONT_S}),
                    dcc.Input(id='input-next', type='text', style={'width': '100%', 'fontSize': FONT_S, 'height': INPUT_H})
                ], style={'marginBottom': '10px'}),
            ], style={'padding': '10px', 'backgroundColor': '#f1f3f5', 'borderRadius': '4px', 'marginBottom': '10px'}),

            # 詳細 (Textarea 高さを抑制)
            html.Div([
                html.Label("Docs / Actions / Lessons", style={'fontWeight': 'bold', 'fontSize': FONT_S, 'color': '#0d6efd'}),
                dcc.Textarea(id='input-doc', placeholder='Documents', style={'width': '100%', 'height': '30px', 'fontSize': FONT_S, 'marginTop': '2px'}),
                dcc.Textarea(id='input-action', placeholder='Actions', style={'width': '100%', 'height': '30px', 'fontSize': FONT_S, 'marginTop': '2px'}),
                dcc.Textarea(id='input-lesson', placeholder='Lessons', style={'width': '100%', 'height': '30px', 'fontSize': FONT_S, 'marginTop': '2px'}),
            ], style={'marginBottom': '10px'}),

            # ボタン
            html.Div([
                html.Button('Add', id='btn-add', style={'width': '30%', 'fontSize': '12px', 'padding': '5px', 'backgroundColor': '#20c997', 'color': 'white', 'border': 'none'}),
                html.Button('Upd', id='btn-update', style={'width': '30%', 'fontSize': '12px', 'padding': '5px', 'marginLeft': '3%', 'backgroundColor': '#0d6efd', 'color': 'white', 'border': 'none'}),
                html.Button('Del', id='btn-delete', style={'width': '30%', 'fontSize': '12px', 'padding': '5px', 'marginLeft': '3%', 'backgroundColor': '#dc3545', 'color': 'white', 'border': 'none'}),
            ], style={'marginBottom': '5px', 'textAlign': 'center'}),
            
            html.Div([
                html.Button('▲', id='btn-up', style={'width': '45%', 'fontSize': '10px', 'padding': '2px'}),
                html.Button('▼', id='btn-down', style={'width': '45%', 'fontSize': '10px', 'padding': '2px', 'marginLeft': '5%'}),
            ], style={'marginBottom': '10px', 'textAlign': 'center'}),

            # テーブル (行数を減らす)
            dash_table.DataTable(
                id='task-table',
                columns=[{"name": "ID", "id": "id"}, {"name": "Task", "id": "task"}, {"name": "Start", "id": "start"}],
                data=current_tasks,
                row_selectable='single',
                selected_rows=[],
                style_cell={'textAlign': 'left', 'fontSize': '11px', 'padding': '5px'},
                style_header={'fontWeight': 'bold', 'backgroundColor': '#e9ecef', 'fontSize': '11px'},
                style_data_conditional=[{'if': {'state': 'active'}, 'backgroundColor': 'rgba(0, 116, 217, 0.3)'}],
                page_size=5 # 5行に制限
            ),
            
            # Mermaid (高さを拡大: 200px)
            html.Div([
                html.Button('Import Mermaid', id='btn-parse', style={'width':'100%', 'fontSize': '10px', 'marginTop': '5px'}),
                dcc.Textarea(id='mermaid-output', style={'width': '100%', 'height': '200px', 'fontSize': '10px', 'fontFamily': 'monospace'}),
            ])

        ], style={'width': '30%', 'padding': '10px', 'boxSizing': 'border-box', 'overflowY': 'auto', 'borderRight': '1px solid #ccc'}),

        # === 右カラム: グラフ (70%) ===
        html.Div([
            dcc.Graph(
                id='gantt-graph', 
                style={'width': '100%', 'height': '100%'}, # 親要素いっぱいに広げる
                config={'responsive': True}
            ),
        ], style={'width': '70%', 'padding': '10px', 'boxSizing': 'border-box', 'height': '100%'}),

    # 高さ 100vh に変更
    ], style={'display': 'flex', 'flexDirection': 'row', 'height': '100vh'}),

    dcc.Store(id='task-store', data=current_tasks),

], style={'height': '100vh', 'overflow': 'hidden', 'fontFamily': 'Arial, sans-serif'}) # スクロール禁止

# --- Callbacks ---
@app.callback(
    [Output('task-store', 'data'), Output('task-table', 'selected_rows')],
    [Input('btn-add', 'n_clicks'), Input('btn-update', 'n_clicks'), Input('btn-delete', 'n_clicks'),
     Input('btn-up', 'n_clicks'), Input('btn-down', 'n_clicks'),
     Input('btn-parse', 'n_clicks'),
     Input('data-selector', 'value'),
     Input('task-table', 'active_cell'),
     Input('gantt-graph', 'clickData')],
    [State('task-store', 'data'), State('task-table', 'selected_rows'), 
     State('input-section', 'value'), State('input-task', 'value'), State('input-start', 'value'), State('input-end', 'value'), State('input-next', 'value'),
     State('input-doc', 'value'), State('input-action', 'value'), State('input-lesson', 'value'),
     State('mermaid-output', 'value')]
)
def update_store(add_n, upd_n, del_n, up_n, down_n, parse_n, selected_data, active_cell, click_data,
                 tasks, selected_rows, section, task, start, end, next_to, 
                 doc, action, lesson, m_code):
    trig = ctx.triggered_id
    if not trig: return tasks, selected_rows

    if trig == 'data-selector':
        return (past_tasks, []) if selected_data == 'past' else (current_tasks, [])

    if trig == 'task-table' and active_cell:
        return tasks, [active_cell['row']]

    if trig == 'gantt-graph' and click_data:
        try:
            point = click_data['points'][0]
            y_pos = point.get('y', 0)
            if isinstance(y_pos, (int, float)):
                task_idx = len(tasks) - 1 - int(y_pos)
                if 0 <= task_idx < len(tasks):
                    return tasks, [task_idx]
        except: pass
        return tasks, selected_rows

    if trig == 'btn-parse':
        lines = m_code.split('\n')
        parsed = []
        curr_sec = "Default"
        cnt = 1
        for line in lines:
            line = line.strip()
            if line.startswith('section'): curr_sec = line.replace('section', '').strip()
            elif ':' in line:
                parts = line.split(':')
                tn = parts[0].strip()
                rem = parts[1].strip()
                tokens = [t.strip() for t in rem.split(',')]
                dates = [t for t in tokens if re.match(r'\d{4}-\d{2}-\d{2}', t)]
                ids = [t for t in tokens if not re.match(r'\d{4}-\d{2}-\d{2}', t) and not t.startswith('after')]
                if len(dates) >= 1:
                    s = dates[0]
                    e = dates[1] if len(dates) > 1 else s
                    tid = ids[0] if ids else f"id{cnt}"
                    parsed.append({"id": tid, "section": curr_sec, "task": tn, "start": s, "end": e, "next_to": "", "doc": "", "action": "", "lesson": ""})
                    cnt += 1
        return (parsed, []) if parsed else (tasks, selected_rows)

    new_tasks = tasks[:]
    idx = selected_rows[0] if selected_rows else None
    new_id = f"t{str(uuid.uuid4())[:4]}"
    task_data = {"section": section, "task": task, "start": start, "end": end, "next_to": next_to or "", "doc": doc or "", "action": action or "", "lesson": lesson or ""}

    if trig == 'btn-add' and section and task:
        task_data["id"] = new_id
        new_tasks.append(task_data)
        return new_tasks, []
    elif trig == 'btn-update' and idx is not None:
        task_data["id"] = new_tasks[idx].get("id", new_id)
        new_tasks[idx] = task_data
        return new_tasks, selected_rows
    elif trig == 'btn-delete' and idx is not None:
        del new_tasks[idx]
        return new_tasks, []
    elif trig == 'btn-up' and idx is not None and idx > 0:
        new_tasks[idx], new_tasks[idx-1] = new_tasks[idx-1], new_tasks[idx]
        return new_tasks, [idx-1]
    elif trig == 'btn-down' and idx is not None and idx < len(new_tasks) - 1:
        new_tasks[idx], new_tasks[idx+1] = new_tasks[idx+1], new_tasks[idx]
        return new_tasks, [idx+1]
            
    return tasks, selected_rows

@app.callback(
    [Output('gantt-graph', 'figure'), Output('task-table', 'data'), Output('mermaid-output', 'value')],
    [Input('task-store', 'data')]
)
def update_view(tasks):
    if not tasks: return go.Figure(), [], ""
    df = pd.DataFrame(tasks)
    df_rev = df.iloc[::-1].reset_index(drop=True)
    fig = go.Figure()
    sections = df['section'].unique()
    colors = px.colors.qualitative.Plotly
    color_map = {s: colors[i % len(colors)] for i, s in enumerate(sections)}
    id_to_coords = {} 
    y_labels = []
    
    for i, row in df_rev.iterrows():
        y_pos = i
        sec = row['section']
        task_name = row['task']
        c = color_map.get(sec, 'gray')
        y_labels.append(f"<b>[{sec}]</b> {task_name}")
        try:
            d_start = pd.to_datetime(row['start'])
            d_end = pd.to_datetime(row['end'])
            s_str = d_start.strftime('%m/%d')
            e_str = d_end.strftime('%m/%d')
        except:
            y_labels.pop()
            continue
        id_to_coords[row['id']] = {"x_start": d_start, "x_end": d_end, "y": y_pos}
        duration = (d_end - d_start).days
        hover_text = f"<b>{task_name}</b> ({sec})<br>{row['start']} - {row['end']}<br>{row.get('lesson', '')}"
        lesson_txt = row.get('lesson', '')
        
        # フォントサイズは少し小さめに
        txt_font = dict(size=11, family='Arial, sans-serif')
        
        if duration <= 0:
            disp_text = f"{s_str}"
            if lesson_txt: disp_text += f"<br>{lesson_txt}"
            fig.add_trace(go.Scatter(
                x=[d_start], y=[y_pos], mode='markers+text',
                marker=dict(symbol='diamond', size=14, color=c, line=dict(width=1, color='black')),
                text=[disp_text], textposition="bottom center", textfont=txt_font,
                name=sec, showlegend=False, hoverinfo='text', hovertext=hover_text, customdata=[row['id']]
            ))
        else:
            disp_text = f"{s_str}-{e_str}"
            if lesson_txt: disp_text += f": {lesson_txt}"
            fig.add_trace(go.Bar(
                x=[duration + 1], y=[y_pos], base=[d_start], orientation='h',
                marker=dict(color=c, opacity=0.8, line=dict(width=1, color=c)),
                text=[disp_text], textposition='outside', cliponaxis=False, textfont=txt_font,
                name=sec, showlegend=False, hoverinfo='text', hovertext=hover_text, customdata=[row['id']]
            ))

    annotations = []
    for t_id, coords in id_to_coords.items():
        task_data = next((t for t in tasks if t.get("id") == t_id), None)
        if not task_data: continue
        target_id = task_data.get("next_to")
        if target_id and target_id in id_to_coords:
            tgt = id_to_coords[target_id]
            src = coords
            annotations.append(dict(
                x=tgt["x_start"], y=tgt["y"], xref="x", yref="y",
                ax=src["x_end"], ay=src["y"], axref="x", ayref="y",
                showarrow=True, arrowhead=2, arrowsize=1, arrowwidth=1, arrowcolor="#555"
            ))

    fig.update_layout(
        title={'text': "Project Schedule", 'y':0.98, 'x':0.5, 'xanchor': 'center', 'font': {'size': 18}}, 
        xaxis=dict(type='date', side='top', gridcolor='#eee', showgrid=True, tickfont=dict(size=11)),
        yaxis=dict(tickmode='array', tickvals=list(range(len(y_labels))), ticktext=y_labels, showgrid=True, gridcolor='#f5f5f5', automargin=True, tickfont=dict(size=11)),
        plot_bgcolor='white',
        autosize=True, # 自動調整
        margin=dict(l=10, r=10, t=60, b=10), # 余白削減
        showlegend=False,
        hoverlabel=dict(bgcolor="white", font_size=12)
    )
    
    lines = ["gantt", "    dateFormat YYYY-MM-DD", "    title Gantt Chart"]
    curr_sec = None
    for t in tasks:
        if t['section'] != curr_sec:
            curr_sec = t['section']
            lines.append(f"    section {curr_sec}")
        lines.append(f"    {t['task']} : {t['id']}, {t['start']}, {t['end']}")

    return fig, tasks, "\n".join(lines)

@app.callback(
    [Output('input-section', 'value'), Output('input-task', 'value'), Output('input-start', 'value'), Output('input-end', 'value'), Output('input-next', 'value'),
     Output('input-doc', 'value'), Output('input-action', 'value'), Output('input-lesson', 'value')],
    Input('task-table', 'selected_rows'), State('task-store', 'data')
)
def fill_form(rows, tasks):
    if not rows: return "", "", str(date.today()), str(date.today()), "", "", "", ""
    t = tasks[rows[0]]
    return t.get('section'), t.get('task'), t.get('start'), t.get('end'), t.get('next_to', ""), t.get('doc', ""), t.get('action', ""), t.get('lesson', "")

def open_browser(): webbrowser.open_new("http://127.0.0.1:8050/")
if __name__ == '__main__':
    Timer(1, open_browser).start()
    app.run(debug=False, port=8050)