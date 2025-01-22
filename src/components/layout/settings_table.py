from fasthtml.components import Div, H2
from shad4fast import (
    Table,
    TableBody,
    TableCell,
    TableHead,
    TableHeader,
    TableRow,
)
from typing import List, Dict, Optional, Any
from src.components.common.heading import SettingsHeading

def SettingsTable(
    title: str, 
    col1_name: str, 
    col2_name: str, 
    items: Optional[List[Dict]] = None,
    row_actions: Optional[List[Any]] = None,
    header_actions: Optional[List[Any]] = None
):
    if items is None:
        items = []
    if row_actions is None:
        row_actions = []
    if header_actions is None:
        header_actions = []
        
    return Div(
        Div(
            Div(
                SettingsHeading(title),
                Div(
                    *header_actions,
                    cls="flex items-center space-x-2"
                ) if header_actions else None,
                cls="flex justify-between items-center mb-8"
            ),
        ),
        Div(
            Table(
                TableHeader(
                    TableRow(
                        TableHead(col1_name, cls="w-2/5 px-6 py-4 text-sm font-medium text-gray-500 dark:text-gray-400 uppercase tracking-wider border-r border-gray-200 dark:border-gray-800 first:rounded-tl-lg"),
                        TableHead(col2_name, cls="w-2/5 px-6 py-4 text-sm font-medium text-gray-500 dark:text-gray-400 uppercase tracking-wider border-r border-gray-200 dark:border-gray-800"),
                        TableHead("Actions", cls="w-1/5 px-6 py-4 text-sm font-medium text-gray-500 dark:text-gray-400 uppercase tracking-wider rounded-tr-lg") if row_actions else None,
                    ),
                    cls="bg-gray-50 dark:bg-gray-800"
                ),
                TableBody(
                    *[
                        TableRow(
                            TableCell(item["col1"], cls="px-6 py-4 text-sm font-medium text-gray-900 dark:text-white border-r border-gray-200 dark:border-gray-800 truncate max-w-0"),
                            TableCell(item["col2"], cls="px-6 py-4 text-sm text-gray-500 dark:text-gray-400 border-r border-gray-200 dark:border-gray-800"),
                            TableCell(
                                *[
                                    action(item["id"]) if callable(action) else action 
                                    for action in row_actions
                                ],
                                cls="px-6 py-4 space-x-2"
                            ) if row_actions else None,
                            cls="bg-white hover:bg-gray-70 dark:bg-gray-900 dark:hover:bg-gray-950",
                            id=f"row-{item['id']}"
                        )
                        for item in items
                    ],
                    cls="divide-y divide-gray-200 dark:divide-gray-800"
                ),
                cls="w-full border border-gray-200 dark:border-gray-800 rounded-lg"
            ) if items else Div(
                "No items found",
                cls="text-center py-8 text-gray-500 dark:text-gray-400"
            ),
            id="settings-table-container",
            cls="w-full bg-white dark:bg-gray-900 shadow rounded-lg overflow-hidden [&_*]:!transition-none"
        ),
        cls="w-full p-6"
    )
