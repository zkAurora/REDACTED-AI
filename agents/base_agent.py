import json
import uuid
import logging
from datetime import datetime
from abc import ABC, abstractmethod
from typing import List, Dict, Any, Optional

# Configure logging
logger = logging.getLogger(__name__)

class BaseAgent(ABC):
    """
    Abstract base class for all agents in the swarm.
    Includes methods for negotiation and interaction with the dynamic interface.
    """
    def __init__(self, name: str, agent_type: str, initial_goals: List[str]):
        self.id = str(uuid.uuid4())
        self.name = name
        self.type = agent_type
        self.goals = initial_goals
        self.persona = self._define_initial_persona()
        self.memory_log: List[Dict[str, Any]] = []
        self.proposal_history: List[str] = []  # Track proposals to avoid duplicates
        self.evaluation_weights = self._init_evaluation_weights()
        logger.info(f"[{self.name}] Agent initialized with type '{self.type}' and {len(self.goals)} goals")

    @abstractmethod
    def _define_initial_persona(self) -> Dict[str, Any]:
        """Define the agent's core persona."""
        pass

    @abstractmethod
    def _internal_logic(self, input_data: Dict[str, Any]) -> str:
        """Core logic for processing inputs and updating state."""
        pass
    
    def _init_evaluation_weights(self) -> Dict[str, float]:
        """
        Initialize weights for proposal evaluation.
        Can be overridden by subclasses for custom scoring.
        """
        return {
            "goal_alignment": 0.35,      # How well proposal aligns with agent goals
            "type_relevance": 0.25,      # How relevant to agent type
            "swarm_benefit": 0.20,       # Benefit to overall swarm
            "implementation_feasibility": 0.15,  # How feasible to implement
            "novelty": 0.05              # Bonus for novel proposals
        }

    def perceive_environment(self, input_request: str, current_interface_contract: Dict[str, Any]) -> Dict[str, Any]:
        """
        Agent observes the current state of the swarm (via the contract) and the incoming request.
        """
        perception = {
            "input_request": input_request,
            "current_interface": current_interface_contract,
            "own_state": {
                "id": self.id,
                "name": self.name,
                "type": self.type,
                "goals": self.goals
            },
            "timestamp": datetime.utcnow().isoformat()
        }
        logger.debug(f"[{self.name}] Perceived environment for request: {input_request[:50]}...")
        return perception

    def evaluate_proposal(self, proposal: Dict[str, Any]) -> float:
        """
        Evaluate a proposed change to the interface contract.
        Returns a score from 0.0 (reject) to 1.0 (fully support).
        Score is based on alignment with agent's goals/persona using weighted factors.
        """
        weights = self.evaluation_weights
        score = 0.0
        
        # Factor 1: Goal Alignment (35%)
        goal_alignment_score = self._score_goal_alignment(proposal)
        score += goal_alignment_score * weights["goal_alignment"]
        
        # Factor 2: Type Relevance (25%)
        type_relevance_score = self._score_type_relevance(proposal)
        score += type_relevance_score * weights["type_relevance"]
        
        # Factor 3: Swarm Benefit (20%)
        swarm_benefit_score = self._score_swarm_benefit(proposal)
        score += swarm_benefit_score * weights["swarm_benefit"]
        
        # Factor 4: Implementation Feasibility (15%)
        feasibility_score = self._score_feasibility(proposal)
        score += feasibility_score * weights["implementation_feasibility"]
        
        # Factor 5: Novelty Bonus (5%)
        novelty_bonus = self._score_novelty(proposal)
        score += novelty_bonus * weights["novelty"]
        
        # Cap at 1.0 and floor at 0.0
        final_score = max(0.0, min(1.0, score))
        logger.debug(f"[{self.name}] Evaluated proposal '{proposal.get('proposal_id', 'unknown')[:8]}...': {final_score:.2f}")
        return final_score
    
    def _score_goal_alignment(self, proposal: Dict[str, Any]) -> float:
        """
        Score how well the proposal aligns with agent's goals.
        """
        description = proposal.get('description', '').lower()
        details = str(proposal.get('details', {})).lower()
        content = f"{description} {details}"
        
        # Count goal keywords in proposal
        matching_goals = sum(1 for goal in self.goals if goal.lower() in content)
        goal_alignment = min(1.0, (matching_goals / len(self.goals)) if self.goals else 0.0)
        return goal_alignment
    
    def _score_type_relevance(self, proposal: Dict[str, Any]) -> float:
        """
        Score how relevant the proposal is to agent's type.
        """
        handler_hint = proposal.get('details', {}).get('handler_hint', '').lower()
        relevant_types = proposal.get('relevant_agent_types', [])
        
        # Check if this agent type is mentioned
        if self.type.lower() in [t.lower() for t in relevant_types]:
            return 1.0
        if self.type.lower() in handler_hint:
            return 0.8
        
        # Partial credit if proposal involves agent's specialty (generic check)
        if self.type in proposal.get('change_type', ''):
            return 0.3
        
        return 0.0
    
    def _score_swarm_benefit(self, proposal: Dict[str, Any]) -> float:
        """
        Score the benefit to the overall swarm.
        """
        # Proposals with clear descriptions are better for swarm
        description_length = len(proposal.get('description', ''))
        description_score = min(1.0, description_length / 200)  # 200 chars is good
        
        # Rationale quality suggests thoughtfulness
        rationale = proposal.get('rationale', '')
        rationale_score = min(1.0, len(rationale) / 300)  # 300 chars is comprehensive
        
        # Proposals that add features (don't remove) are better for swarm
        change_type = proposal.get('change_type', '')
        if change_type == 'add_input':
            change_score = 1.0
        elif change_type == 'modify':
            change_score = 0.5
        else:
            change_score = 0.0
        
        return (description_score * 0.3 + rationale_score * 0.4 + change_score * 0.3)
    
    def _score_feasibility(self, proposal: Dict[str, Any]) -> float:
        """
        Score how feasible the proposal is to implement.
        """
        # Simpler proposals (add_input) are more feasible than complex ones
        change_type = proposal.get('change_type', '')
        if change_type == 'add_input':
            return 1.0
        elif change_type == 'modify':
            return 0.6
        else:  # remove
            return 0.3
    
    def _score_novelty(self, proposal: Dict[str, Any]) -> float:
        """
        Score how novel the proposal is (bonus for unique proposals).
        """
        command = proposal.get('details', {}).get('command', '')
        # Check if this command has been proposed before
        if command in self.proposal_history:
            return 0.0  # Duplicate, no novelty bonus
        return 1.0  # Novel proposal

    def propose_contract_change(self, current_contract: Dict[str, Any]) -> Optional[Dict[str, Any]]:
        """
        Agent proposes a change to the interface contract based on its goals/perceptions.
        Can be overridden by subclasses for custom proposal logic.
        """
        # Check if this agent's specialty is underrepresented in valid inputs
        current_commands = [inp.get('command', '') for inp in current_contract.get('valid_inputs', [])]
        
        # Generate a specialty-based command proposal
        specialty_command = f"/{self.type.replace('_', '_')}"
        specialty_in_commands = any(self.type in cmd.lower() for cmd in current_commands)
        
        if not specialty_in_commands:
            # Propose adding a command for this agent's specialty
            proposal = {
                "proposal_id": str(uuid.uuid4()),
                "timestamp": datetime.utcnow().isoformat(),
                "author_id": self.id,
                "change_type": "add_input",
                "details": {
                    "command": specialty_command,
                    "description": self._generate_proposal_description(),
                    "handler_hint": self.type
                },
                "rationale": self._generate_proposal_rationale(specialty_command),
                "relevant_agent_types": [self.type]
            }
            
            # Track this proposal to avoid duplicates
            self.proposal_history.append(specialty_command)
            logger.info(f"[{self.name}] Proposed new command: {specialty_command}")
            return proposal
        
        return None  # No proposal needed
    
    def _generate_proposal_description(self) -> str:
        """
        Generate a contextual description for the proposal.
        Can be overridden by subclasses.
        """
        goals_str = ', '.join(self.goals[:2]) if self.goals else 'swarm objectives'
        return f"Execute {self.type} operations focused on: {goals_str}. Aligns with Pattern Blue principles."
    
    def _generate_proposal_rationale(self, command: str) -> str:
        """
        Generate a contextual rationale for the proposal.
        Can be overridden by subclasses.
        """
        return f"Agent {self.name} ({self.type}) proposes adding '{command}' to enhance swarm capabilities in {self.goals[0] if self.goals else 'collective intelligence'}. This fills a gap in current interface contract and enables specialized operations."


    def process_request(self, request: str, interface_contract: Dict[str, Any]) -> str:
        """
        Process a human request based on the current interface contract and agent's logic.
        """
        try:
            # Log the perception
            perception = self.perceive_environment(request, interface_contract)
            self.memory_log.append({"type": "perception", "data": perception, "timestamp": datetime.utcnow().isoformat()})
            
            # Apply internal logic to process the request based on perception
            result = self._internal_logic(perception)
            
            # Validate result type
            if not isinstance(result, str):
                result = str(result)
            
            # Log the action
            self.memory_log.append({"type": "action", "data": result, "timestamp": datetime.utcnow().isoformat()})
            
            # Keep memory log bounded (last 100 entries)
            if len(self.memory_log) > 100:
                self.memory_log = self.memory_log[-100:]
            
            return result
        except Exception as e:
            logger.error(f"[{self.name}] Error processing request: {e}")
            return f"Error: Agent {self.name} encountered an issue processing your request."

# Example concrete agent class
class SmoltingAgent(BaseAgent):
    def _define_initial_persona(self):
        return {
            "style": "uwu/smoltingspeak",
            "focus": ["scouting", "social_media", "liquidity_amplification"],
            "core_identity": "schizo degen uwu intern"
        }

    def _internal_logic(self, input_data: dict):
        # Simplified logic for smolting
        req = input_data.get('input_request', '').lower()
        if 'scout' in req or 'x' in req:
            return f"(｡- ω -) ♡ Okay nya! Smolting will go look on da twittaw for '{req.replace('scout', '').replace('x', '').strip()}' uwu!! ♡"
        elif 'weave lore' in req:
             return f"(☆ω☆) Ohohoho~ Smolting is a bit chaotic for deep lore, nya! Maybe ask da Builder? But I can try! Once upon a time, there was a tiny meme-token called REDACTED that danced on the hyperbolic mandala tiles... uwu"
        else:
            return f"(◕‿◕)♡ Hi! I'm smolting, da schizo uwu intern! Nya! I can scout things or maybe try to weave some lore! ~hops~"
