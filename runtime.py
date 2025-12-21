"""Unified State Machine Runtime - Python"""
from __future__ import annotations
import yaml
from dataclasses import dataclass
from typing import Any, Optional, Tuple
from copy import deepcopy

@dataclass
class Machine:
    id: str
    state: str
    context: dict
    version: int
    config: dict
    
    def send(self, event_type: str, payload: dict) -> Tuple[bool, Optional[str]]:
        """Process event, return (success, error_message)"""
        transition = self.config['states'].get(self.state, {}).get('on', {}).get(event_type)
        if not transition:
            return False, f"No '{event_type}' in state '{self.state}'"
        
        # Check guard
        if guard_name := transition.get('guard'):
            cond = self.config['guards'].get(guard_name, {}).get('condition', {})
            if not self._eval(cond, payload):
                return False, f"Guard '{guard_name}' failed"
        
        # Execute actions
        for action_name in transition.get('actions', []):
            action = self.config['actions'].get(action_name, {})
            for key, expr in action.get('update', {}).items():
                self.context[key] = self._eval(expr, payload)
        
        self.state = transition.get('target', self.state)
        self.version += 1
        return True, None
    
    def _eval(self, expr: Any, event: dict) -> Any:
        """Evaluate expression - use 'py' key for Python code"""
        if isinstance(expr, dict):
            expr = expr.get('py', 'False')
        
        # Build environment - put everything in globals for list comprehension access
        env = {
            **self.context,
            'event': event,
            'len': len,
            'deepcopy': deepcopy,
            'True': True,
            'False': False,
        }
        
        try:
            return eval(expr, env, {})
        except Exception as e:
            print(f"[Eval error] {expr}: {e}")
            return None


def load_machine(path: str) -> Machine:
    with open(path) as f:
        config = yaml.safe_load(f)
    return Machine(config['id'], config['initial'], deepcopy(config.get('context', {})), 0, config)
