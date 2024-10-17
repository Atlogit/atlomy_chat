import argparse
import json
from typing import List, Optional
from .lexical_value_generator import LexicalValueGenerator
from .lexical_value import LexicalValue
from .corpus_manager import CorpusManager
from .logging_config import logger

class LexicalValueCLI:
    def __init__(self, generator: LexicalValueGenerator):
        self.generator = generator
        logger.info("LexicalValueCLI initialized")

    def list_lexical_values(self) -> List[dict]:
        logger.info("Listing all lexical values")
        lemmas = self.generator.list_lexical_values()
        result = [{"lemma": lv.lemma, "short_description": lv.short_description} 
                  for lv in [self.generator.get_lexical_value(lemma) for lemma in lemmas] if lv]
        logger.info(f"Found {len(result)} lexical values")
        return result

    def view_lexical_value(self, lemma: str) -> Optional[dict]:
        logger.info(f"Viewing lexical value for lemma: {lemma}")
        lv = self.generator.get_lexical_value(lemma)
        if lv:
            result = lv.__dict__.copy()
            suggestions = self.generator.suggest_updates(lemma, "")
            if suggestions:
                result["suggested_updates"] = suggestions
            logger.info(f"Retrieved lexical value for lemma: {lemma}")
            return result
        logger.warning(f"Lexical value not found for lemma: {lemma}")
        return None

    def edit_lexical_value(self, lemma: str, **kwargs) -> None:
        logger.info(f"Editing lexical value for lemma: {lemma}")
        lv = self.generator.get_lexical_value(lemma)
        if lv:
            for key, value in kwargs.items():
                if hasattr(lv, key):
                    setattr(lv, key, value)
            self.generator.update_lexical_value(lv)
            logger.info(f"Updated lexical value for lemma: {lemma}")
        else:
            logger.error(f"Lexical value not found for lemma: {lemma}")
            raise ValueError(f"Lexical value for '{lemma}' not found.")

    def suggest_updates(self, lemma: str, new_text: str) -> dict:
        logger.info(f"Suggesting updates for lemma: {lemma}")
        suggestions = self.generator.suggest_updates(lemma, new_text)
        logger.info(f"Generated suggestions for lemma: {lemma}")
        return suggestions

    def view_version_history(self, lemma: str) -> List[dict]:
        logger.info(f"Viewing version history for lemma: {lemma}")
        history = self.generator.get_version_history(lemma)
        logger.info(f"Retrieved {len(history)} versions for lemma: {lemma}")
        return [version.__dict__ for version in history]

def main():
    parser = argparse.ArgumentParser(description="Lexical Value CLI")
    parser.add_argument('action', choices=['list', 'view', 'edit', 'suggest', 'history'])
    parser.add_argument('--lemma', help="Lemma of the lexical value")
    parser.add_argument('--fields', help="Fields to edit (for edit action), comma-separated")
    parser.add_argument('--values', help="New values (for edit action), comma-separated")
    parser.add_argument('--new-text', help="New text for suggestion (for suggest action)")

    args = parser.parse_args()

    corpus_manager = CorpusManager()
    generator = LexicalValueGenerator(corpus_manager)
    cli = LexicalValueCLI(generator)

    try:
        if args.action == 'list':
            lemmas = cli.list_lexical_values()
            print("Available lemmas:")
            for item in lemmas:
                print(f"- {item['lemma']}: {item['short_description']}")

        elif args.action == 'view':
            if not args.lemma:
                logger.error("--lemma is required for view action")
                raise ValueError("--lemma is required for view action")
            lv = cli.view_lexical_value(args.lemma)
            if lv:
                print(json.dumps(lv, indent=2))
            else:
                print(f"Lexical value for '{args.lemma}' not found.")

        elif args.action == 'edit':
            if not args.lemma or not args.fields or not args.values:
                logger.error("--lemma, --fields, and --values are required for edit action")
                raise ValueError("--lemma, --fields, and --values are required for edit action")
            fields = args.fields.split(',')
            values = args.values.split(',')
            if len(fields) != len(values):
                logger.error("Number of fields must match number of values")
                raise ValueError("Number of fields must match number of values")
            cli.edit_lexical_value(args.lemma, **dict(zip(fields, values)))
            print(f"Updated {', '.join(fields)} for '{args.lemma}'")

        elif args.action == 'suggest':
            if not args.lemma or not args.new_text:
                logger.error("--lemma and --new-text are required for suggest action")
                raise ValueError("--lemma and --new-text are required for suggest action")
            suggestions = cli.suggest_updates(args.lemma, args.new_text)
            print("Suggested updates:")
            print(json.dumps(suggestions, indent=2))

        elif args.action == 'history':
            if not args.lemma:
                logger.error("--lemma is required for history action")
                raise ValueError("--lemma is required for history action")
            history = cli.view_version_history(args.lemma)
            print(f"Version history for '{args.lemma}':")
            for version in history:
                print(f"Version {version['version']}:")
                print(json.dumps({k: v for k, v in version.items() if k != 'version'}, indent=2))
                print()

    except Exception as e:
        logger.exception(f"An error occurred: {str(e)}")
        print(f"Error: {str(e)}")

if __name__ == "__main__":
    main()
