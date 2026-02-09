"""
Workflow Visualization - Flask App with DAG and Timeline PNG Generation
既存の Dash UI 構造を保持しながら Flask で実装
左：コントロールパネル (30%) / 右：ガントチャート (70%)

完全な仕様準拠:
- DAG PNG生成と静的ファイル配信
- Timeline PNG生成と静的ファイル配信
- /validate エンドポイント（検証結果表示）
- /knowledge/<node_id> エンドポイント（Markdown→HTML）
- 完全なフォーム処理（JavaScript不要）
"""

import json
import os
import re
import traceback
from collections import defaultdict
from datetime import datetime
from pathlib import Path

import markdown
import pandas as pd
from flask import (
    Flask,
    redirect,
    render_template,
    request,
    send_file,
    send_from_directory,
    url_for,
)

# ==================== VALIDATION ENGINE ====================


class ValidationError(Exception):
    pass


def validate_workflow(nodes):
    errors = []
    warnings = []
    node_by_id = {node["id"]: node for node in nodes}

    # 存在しない依存関係のチェック
    for node in nodes:
        for dep_id in node.get("depends_on", []):
            if dep_id not in node_by_id:
                errors.append(
                    f"Node '{node['id']}': Dependency '{dep_id}' does not exist"
                )

    # サイクル検出
    cycle_errors = detect_cycles(nodes, node_by_id)
    errors.extend(cycle_errors)

    # 期限矛盾チェック
    deadline_errors = check_deadline_contradictions(nodes, node_by_id)
    warnings.extend(deadline_errors)

    return {"valid": len(errors) == 0, "errors": errors, "warnings": warnings}


def check_deadline_contradictions(nodes, node_by_id):
    """親ノードの期限が子ノードより古い場合は警告"""
    warnings = []
    for node in nodes:
        try:
            parent_date = datetime.strptime(node.get("deadline", ""), "%Y-%m-%d")
        except:
            continue

        for dep_id in node.get("depends_on", []):
            parent_node = node_by_id.get(dep_id)
            if parent_node:
                try:
                    dep_date = datetime.strptime(
                        parent_node.get("deadline", ""), "%Y-%m-%d"
                    )
                    if dep_date > parent_date:
                        warnings.append(
                            f"Deadline contradiction: '{dep_id}' (親) has deadline {parent_node['deadline']} "
                            f"but '{node['id']}' (子) has earlier deadline {node['deadline']}"
                        )
                except:
                    pass

    return warnings


def detect_cycles(nodes, node_by_id):
    errors = []
    graph = defaultdict(list)
    for node in nodes:
        for dep_id in node.get("depends_on", []):
            graph[dep_id].append(node["id"])

    visited = set()
    rec_stack = set()

    def has_cycle(node_id, path):
        visited.add(node_id)
        rec_stack.add(node_id)

        for neighbor in graph.get(node_id, []):
            if neighbor not in visited:
                if has_cycle(neighbor, path + [node_id]):
                    return True
            elif neighbor in rec_stack:
                cycle_path = path + [node_id, neighbor]
                errors.append(f"Cycle detected: {' -> '.join(cycle_path)}")
                return True

        rec_stack.remove(node_id)
        return False

    for node in nodes:
        if node["id"] not in visited:
            has_cycle(node["id"], [])

    return errors


# ==================== DAG GENERATOR ====================


def generate_dag_svg(nodes, section_filter=None):
    """networkxを使ってSVG形式でDAGを生成
    section_filter: セクション名を指定すると、そのセクションのノードのみを表示
    """
    try:
        import networkx as nx

        # セクションでフィルタ
        if section_filter:
            filtered_nodes = [n for n in nodes if n.get("section") == section_filter]
        else:
            filtered_nodes = nodes

        G = nx.DiGraph()

        for node in filtered_nodes:
            G.add_node(node["id"], label=node["label"])

        for node in filtered_nodes:
            for dep_id in node.get("depends_on", []):
                # 依存先がフィルタ済みノードに含まれる場合のみエッジを追加
                if any(n["id"] == dep_id for n in filtered_nodes):
                    G.add_edge(node["id"], dep_id)

        # 階層的レイアウトを使用
        try:
            from networkx.drawing.nx_agraph import graphviz_layout

            pos = graphviz_layout(G, prog="dot")
        except:
            pos = nx.spring_layout(G, k=3, iterations=50, seed=42)

        # SVG生成
        width, height = 1000, 800

        # ノード位置を正規化
        if pos:
            xs = [p[0] for p in pos.values()]
            ys = [p[1] for p in pos.values()]
            min_x, max_x = min(xs), max(xs)
            min_y, max_y = min(ys), max(ys)

            margin = 60
            scale_x = (width - 2 * margin) / (max_x - min_x) if max_x != min_x else 1
            scale_y = (height - 2 * margin) / (max_y - min_y) if max_y != min_y else 1

            normalized_pos = {}
            for node_id, (x, y) in pos.items():
                nx_pos = margin + (x - min_x) * scale_x
                ny_pos = margin + (y - min_y) * scale_y
                normalized_pos[node_id] = (nx_pos, ny_pos)
        else:
            normalized_pos = {}

        # SVG開始
        svg = f'<svg width="{width}" height="{height}" xmlns="http://www.w3.org/2000/svg">'
        svg += '<defs><marker id="arrowhead" markerWidth="10" markerHeight="7" refX="9" refY="3.5" orient="auto">'
        svg += '<polygon points="0 0, 10 3.5, 0 7" fill="#666" class="dag-arrow-marker" data-node-id="marker"/></marker></defs>'

        # エッジ描画
        for edge in G.edges():
            from_node, to_node = edge
            if from_node in normalized_pos and to_node in normalized_pos:
                x1, y1 = normalized_pos[from_node]
                x2, y2 = normalized_pos[to_node]

                # 矢印が長方形の端で終わるように調整
                dx, dy = x2 - x1, y2 - y1
                length = (dx**2 + dy**2) ** 0.5
                if length > 0:
                    x2 = x2 - (dx / length) * 40
                    y2 = y2 - (dy / length) * 15

                svg += f'<line x1="{x1}" y1="{y1}" x2="{x2}" y2="{y2}" '
                svg += 'stroke="#666" stroke-width="2" marker-end="url(#arrowhead)" '
                svg += f'class="dag-edge" data-from="{from_node}" data-to="{to_node}"/>'

        # ノード描画
        for node_id, (x, y) in normalized_pos.items():
            node_data = next((n for n in filtered_nodes if n["id"] == node_id), None)
            label = node_data["label"][:20] if node_data else node_id

            svg += f'<g class="dag-node" data-node-id="{node_id}">'
            svg += f'<rect x="{x - 50}" y="{y - 20}" width="100" height="40" '
            svg += 'fill="#4ECDC4" stroke="#333" stroke-width="2" rx="5"/>'
            svg += f'<text x="{x}" y="{y - 5}" text-anchor="middle" fill="#333" font-size="11" font-weight="bold">{node_id}</text>'
            svg += f'<text x="{x}" y="{y + 10}" text-anchor="middle" fill="#333" font-size="9">{label[:15]}</text>'
            svg += "</g>"

        svg += "</svg>"
        return svg
    except Exception as e:
        print(f"DAG SVG generation error: {e}")
        traceback.print_exc()
        return None


def generate_dag_png(nodes):
    """Graphviz/networkxを使ったDAG PNG生成"""
    try:
        import pygraphviz as pgv

        use_graphviz = True
    except ImportError:
        use_graphviz = False

    if use_graphviz:
        try:
            G = pgv.AGraph(directed=True)
            G.graph_attr["rankdir"] = "TB"
            G.graph_attr["size"] = "12,8"
            G.graph_attr["ratio"] = "fill"

            for node in nodes:
                G.add_node(
                    node["id"],
                    label=node["label"][:20],
                    shape="box",
                    style="filled",
                    fillcolor="lightblue",
                )

            for node in nodes:
                for dep_id in node.get("depends_on", []):
                    G.add_edge(dep_id, node["id"])

            output_path = BASE_DIR / "static" / "dag.png"
            output_path.parent.mkdir(parents=True, exist_ok=True)
            G.draw(str(output_path), prog="dot", format="png")
            return str(output_path)
        except Exception as e:
            print(f"Graphviz error: {e}")
            return None
    else:
        # networkx + matplotlib fallback
        try:
            import matplotlib.pyplot as plt
            import networkx as nx
            from matplotlib.patches import FancyBboxPatch

            G = nx.DiGraph()

            for node in nodes:
                G.add_node(node["id"], label=node["label"])

            for node in nodes:
                for dep_id in node.get("depends_on", []):
                    G.add_edge(dep_id, node["id"])

            pos = nx.spring_layout(G, k=2, iterations=50)

            fig, ax = plt.subplots(1, 1, figsize=(14, 10))

            # ノード描画
            for node_id, (x, y) in pos.items():
                label = [n["label"] for n in nodes if n["id"] == node_id][0]
                bbox = FancyBboxPatch(
                    (x - 0.08, y - 0.04),
                    0.16,
                    0.08,
                    boxstyle="round,pad=0.01",
                    edgecolor="black",
                    facecolor="lightblue",
                )
                ax.add_patch(bbox)
                ax.text(
                    x, y, node_id, ha="center", va="center", fontsize=9, weight="bold"
                )

            # エッジ描画
            nx.draw_networkx_edges(G, pos, ax=ax, arrowsize=20, arrowstyle="->")

            ax.set_xlim(-1.2, 1.2)
            ax.set_ylim(-1.2, 1.2)
            ax.axis("off")
            ax.set_title("Workflow DAG", fontsize=14, weight="bold")

            output_path = BASE_DIR / "static" / "dag.png"
            output_path.parent.mkdir(parents=True, exist_ok=True)
            plt.tight_layout()
            plt.savefig(str(output_path), dpi=100, bbox_inches="tight")
            plt.close()
            return str(output_path)
        except Exception as e:
            print(f"networkx error: {e}")
            return None


def generate_timeline_png(tasks):
    """matplotlib を使ったタイムライン/ガントチャートPNG生成"""
    try:
        import matplotlib.dates as mdates
        import matplotlib.pyplot as plt
        from matplotlib.patches import Rectangle

        if not tasks:
            return None

        df = pd.DataFrame(tasks)

        fig, ax = plt.subplots(figsize=(14, 10))

        sections = df["section"].unique() if "section" in df.columns else ["Default"]
        colors_list = [
            "#FF6B6B",
            "#4ECDC4",
            "#45B7D1",
            "#FFA07A",
            "#98D8C8",
            "#F7DC6F",
            "#BB8FCE",
            "#85C1E2",
        ]
        color_map = {
            s: colors_list[i % len(colors_list)] for i, s in enumerate(sections)
        }

        y_pos = 0
        y_labels = []
        y_ticks = []

        for _, row in df.iterrows():
            try:
                start_date = pd.to_datetime(row["start"])
                end_date = pd.to_datetime(row["end"])
            except:
                continue

            duration_days = (end_date - start_date).days + 1
            section = row.get("section", "Default")
            task_name = row["task"]
            color = color_map.get(section, "gray")

            # バー表示（最短1日）
            rect = Rectangle(
                (start_date, y_pos - 0.3),
                max(1, duration_days),
                0.6,
                facecolor=color,
                edgecolor="black",
                linewidth=1,
                alpha=0.8,
            )
            ax.add_patch(rect)

            y_labels.append(f"{section} - {task_name}")
            y_ticks.append(y_pos)
            y_pos += 1

        ax.set_yticks(y_ticks)
        ax.set_yticklabels(y_labels, fontsize=9)
        ax.xaxis.set_major_formatter(mdates.DateFormatter("%Y-%m-%d"))
        ax.xaxis.set_major_locator(mdates.MonthLocator())
        plt.xticks(rotation=45, ha="right")

        ax.set_xlabel("Date", fontsize=11, weight="bold")
        ax.set_ylabel("Tasks", fontsize=11, weight="bold")
        ax.set_title("Project Timeline (Gantt Chart)", fontsize=14, weight="bold")
        ax.grid(True, axis="x", alpha=0.3)

        ax.set_ylim(-1, y_pos)

        output_path = BASE_DIR / "static" / "timeline.png"
        output_path.parent.mkdir(parents=True, exist_ok=True)
        plt.tight_layout()
        plt.savefig(str(output_path), dpi=100, bbox_inches="tight")
        plt.close()
        return str(output_path)
    except Exception as e:
        print(f"Timeline PNG generation error: {e}")
        traceback.print_exc()
        return None


# ==================== FLASK APPLICATION ====================

app = Flask(__name__, template_folder="templates", static_folder="static")

BASE_DIR = Path(__file__).parent
WORKFLOW_JSON = BASE_DIR / "data" / "workflow.json"


def load_workflow():
    """workflow.json を読み込む"""
    if WORKFLOW_JSON.exists():
        with open(WORKFLOW_JSON, "r", encoding="utf-8") as f:
            return json.load(f)
    return {"nodes": []}


def save_workflow(workflow):
    """workflow.json に保存"""
    WORKFLOW_JSON.parent.mkdir(parents=True, exist_ok=True)
    with open(WORKFLOW_JSON, "w", encoding="utf-8") as f:
        json.dump(workflow, f, ensure_ascii=False, indent=2)


def load_tasks_from_nodes(nodes):
    """ノードをタスク形式に変換"""
    tasks = []
    for node in nodes:
        task = {
            "id": node["id"],
            "section": node.get("section", ""),
            "task": node["label"],
            "start": node.get("deadline", ""),
            "end": node.get("deadline", ""),
            "next_to": node["depends_on"][0] if node.get("depends_on") else "",
            "doc": node.get("doc", ""),
            "action": node.get("action", ""),
            "lesson": node.get("note", ""),
            "qms_path": node.get("qms_path", ""),
            "knowledge_dir": node.get("knowledge_dir", ""),
            "decision": node.get("decision", False),
        }
        tasks.append(task)
    return tasks


def build_knowledge_file_links(knowledge_dir_value):
    if not knowledge_dir_value:
        return []

    knowledge_dir = Path(knowledge_dir_value)
    if not knowledge_dir.is_absolute():
        knowledge_dir = BASE_DIR / knowledge_dir

    try:
        knowledge_dir = knowledge_dir.resolve()
    except Exception:
        return []

    static_root = (BASE_DIR / "static").resolve()
    try:
        common_root = os.path.commonpath([str(static_root), str(knowledge_dir)])
    except ValueError:
        return []

    if common_root != str(static_root):
        return []

    if not knowledge_dir.exists() or not knowledge_dir.is_dir():
        return []

    links = []
    for path in sorted(knowledge_dir.rglob("*")):
        if not path.is_file():
            continue
        try:
            rel_to_static = path.resolve().relative_to(static_root).as_posix()
            rel_to_knowledge = path.resolve().relative_to(knowledge_dir).as_posix()
        except Exception:
            continue
        links.append(
            {
                "label": rel_to_knowledge,
                "url": f"/static/{rel_to_static}",
            }
        )
    return links


def save_nodes_from_tasks(tasks):
    """タスクをノード形式に変換して保存"""
    nodes = []
    for task in tasks:
        node = {
            "id": task["id"],
            "label": task["task"],
            "deadline": task.get("end", task.get("start", "")),
            "decision": task.get("decision", False),
            "note": task.get("lesson", ""),
            "depends_on": [task["next_to"]] if task.get("next_to") else [],
            "qms_path": task.get("qms_path", ""),
            "knowledge_dir": task.get("knowledge_dir", ""),
            "section": task.get("section", ""),
            "doc": task.get("doc", ""),
            "action": task.get("action", ""),
        }
        nodes.append(node)

    workflow = {"nodes": nodes}
    save_workflow(workflow)


def regenerate_images():
    """DAGとタイムラインPNGを再生成"""
    workflow = load_workflow()
    nodes = workflow.get("nodes", [])
    tasks = load_tasks_from_nodes(nodes)

    generate_dag_png(nodes)
    generate_timeline_png(tasks)


@app.route("/")
def index():
    """メイン画面"""
    workflow = load_workflow()
    nodes = workflow.get("nodes", [])
    tasks = load_tasks_from_nodes(nodes)

    # セクション一覧を抽出
    all_sections = sorted(
        list(set(t.get("section", "") for t in tasks if t.get("section")))
    )

    # セクションフィルタを取得
    selected_section = request.args.get("section", "")

    # フィルタリング
    if selected_section and selected_section != "all":
        filtered_tasks = [t for t in tasks if t.get("section") == selected_section]
    else:
        filtered_tasks = tasks

    # 全タスクにknowledge_filesを付与
    for task in filtered_tasks:
        task["knowledge_files"] = build_knowledge_file_links(
            task.get("knowledge_dir", "")
        )

    # Mermaidコード生成
    lines = ["gantt", "    dateFormat YYYY-MM-DD", "    title Gantt Chart"]
    curr_sec = None
    for t in filtered_tasks:
        if t["section"] != curr_sec:
            curr_sec = t["section"]
            lines.append(f"    section {curr_sec}")
        lines.append(f"    {t['task']} : {t['id']}, {t['start']}, {t['end']}")
    mermaid_code = "\n".join(lines)

    # DAG SVG生成（セクションでフィルタ）
    section_filter = (
        selected_section if selected_section and selected_section != "all" else None
    )
    dag_svg = generate_dag_svg(nodes, section_filter)

    return render_template(
        "index.html",
        tasks=filtered_tasks,
        all_tasks=tasks,
        nodes=nodes,
        mermaid_code=mermaid_code,
        all_sections=all_sections,
        selected_section=selected_section,
        dag_svg=dag_svg,
    )


@app.route("/update", methods=["POST"])
def update():
    """フォーム送信でデータ更新"""
    try:
        # フォームデータを取得
        tasks = []

        workflow = load_workflow()
        nodes = workflow.get("nodes", [])

        # フォームの各タスク行を処理
        i = 0
        while f"id_{i}" in request.form:
            task = {
                "id": request.form.get(f"id_{i}", ""),
                "section": request.form.get(f"section_{i}", ""),
                "task": request.form.get(f"task_{i}", ""),
                "start": request.form.get(f"start_{i}", ""),
                "end": request.form.get(f"end_{i}", ""),
                "next_to": request.form.get(f"next_to_{i}", ""),
                "doc": request.form.get(f"doc_{i}", ""),
                "action": request.form.get(f"action_{i}", ""),
                "lesson": request.form.get(f"lesson_{i}", ""),
                "qms_path": request.form.get(f"qms_path_{i}", ""),
                "knowledge_dir": request.form.get(f"knowledge_dir_{i}", ""),
                "decision": "decision_" + str(i) in request.form,
            }
            tasks.append(task)
            i += 1

        if tasks:
            save_nodes_from_tasks(tasks)

        # PNGを再生成
        regenerate_images()

        return redirect(url_for("index"))
    except Exception as e:
        return f"Error: {str(e)}", 400


@app.route("/validate", methods=["GET", "POST"])
def validate():
    """検証結果表示"""
    workflow = load_workflow()
    nodes = workflow.get("nodes", [])
    validation_result = validate_workflow(nodes)

    return render_template("validate.html", result=validation_result, nodes=nodes)


@app.route("/dag.png")
def dag_png():
    """DAG PNG ファイル配信"""
    dag_file = BASE_DIR / "static" / "dag.png"
    if dag_file.exists():
        return send_file(str(dag_file), mimetype="image/png")
    return "DAG not generated yet", 404


@app.route("/timeline.png")
def timeline_png():
    """Timeline PNG ファイル配信"""
    timeline_file = BASE_DIR / "static" / "timeline.png"
    if timeline_file.exists():
        return send_file(str(timeline_file), mimetype="image/png")
    return "Timeline not generated yet", 404


@app.route("/knowledge/<node_id>")
def knowledge(node_id):
    """ナレッジビュー（Markdown → HTML）"""
    workflow = load_workflow()
    nodes = workflow.get("nodes", [])
    node = next((n for n in nodes if n["id"] == node_id), None)

    if not node:
        return "Node not found", 404

    # knowledge_dir を確認して markdown ファイルを探す
    knowledge_dir = Path(node.get("knowledge_dir", ""))
    md_content = ""

    # 相対パスを絶対パスに変換
    if not knowledge_dir.is_absolute():
        knowledge_dir = BASE_DIR / knowledge_dir

    try:
        if knowledge_dir.exists() and knowledge_dir.is_dir():
            # ディレクトリ内の .md ファイルを探す
            md_files = list(knowledge_dir.glob("*.md"))
            if md_files:
                with open(md_files[0], "r", encoding="utf-8") as f:
                    md_content = f.read()
            else:
                print(f"No .md files found in {knowledge_dir}")
        else:
            print(f"Knowledge directory not found: {knowledge_dir}")
    except Exception as e:
        print(f"Error reading knowledge directory {knowledge_dir}: {e}")

    html_content = (
        markdown.markdown(md_content)
        if md_content
        else f"<p>No knowledge found for {node_id}</p>"
    )

    if md_content:
        knowledge_dir_str = node.get("knowledge_dir", "").replace("\\", "/").strip("/")
        if knowledge_dir_str:
            base_url = f"/{knowledge_dir_str}/"

            def _rewrite_link(match):
                prefix, url, suffix = match.group(1), match.group(2), match.group(3)
                if url.startswith(("http://", "https://", "/", "#", "mailto:", "tel:")):
                    return match.group(0)
                if url.startswith("./"):
                    url = url[2:]
                return f"{prefix}{base_url}{url}{suffix}"

            html_content = re.sub(
                r'((?:src|href)=["\'])([^"\']+)(["\'])',
                _rewrite_link,
                html_content,
            )

    return render_template(
        "knowledge.html",
        node_id=node_id,
        node_label=node["label"],
        content=html_content,
    )


@app.route("/static/<path:filename>")
def static_file(filename):
    """静的ファイル配信"""
    return send_from_directory(app.static_folder, filename)


if __name__ == "__main__":
    # 起動時にPNG生成
    print("Generating DAG and Timeline images on startup...")
    regenerate_images()
    print("Images generated successfully.")

    app.run(debug=True, host="127.0.0.1", port=5000)
