from symbolic_ir.data.citation import generate_citation_examples
from symbolic_ir.identifiers import render_identifiers
from symbolic_ir.mechinterp.similarity import cosine_similarity
from symbolic_ir.mechinterp.spans import find_after, token_positions_for_char_span
from symbolic_ir.mechinterp.swaps import swap_source_identifiers
from symbolic_ir.tokenization import RegexTokenCounter


def test_swap_changes_binding_not_identifier_set():
    example = generate_citation_examples(seed=2, count=1, num_sources=5)[0]
    mapping = render_identifiers(example.sources, "structured", 2, RegexTokenCounter())
    left, right = example.sources[0].key, example.sources[1].key
    swapped = swap_source_identifiers(mapping, left, right)
    assert swapped.display_by_source[left] == mapping.display_by_source[right]
    assert set(swapped.display_by_source.values()) == set(mapping.display_by_source.values())


def test_cosine_similarity():
    assert abs(cosine_similarity([1, 0], [1, 0]) - 1.0) < 1e-12
    assert abs(cosine_similarity([1, 0], [0, 1])) < 1e-12


def test_character_spans_map_to_overlapping_tokens():
    offsets = [(0, 0), (0, 3), (3, 5), (6, 10), (0, 0)]
    assert token_positions_for_char_span(offsets, 2, 7) == [1, 2, 3]


def test_find_after_respects_boundary():
    text = "label first label second"
    assert find_after(text, "label", 6) == (12, 17)


def test_position_activation_patch_uses_donor_positions_across_batch():
    import torch

    from symbolic_ir.mechinterp.patching import PositionActivationPatcher, PositionActivationRecorder

    class Tiny(torch.nn.Module):
        def __init__(self):
            super().__init__()
            self.block = torch.nn.Identity()

        def forward(self, value):
            return self.block(value)

    model = Tiny()
    donor = torch.arange(24, dtype=torch.float32).reshape(1, 4, 6)
    with PositionActivationRecorder(model, "block", [1, 3]) as recorder:
        model(donor)
    recipient = torch.zeros(2, 4, 6)
    with PositionActivationPatcher(model, "block", recorder.activation, [0, 2]):
        patched = model(recipient)
    assert torch.equal(patched[0, 0], donor[0, 1])
    assert torch.equal(patched[1, 2], donor[0, 3])
    assert torch.equal(patched[:, 1], torch.zeros(2, 6))


def test_batch_position_activation_patch_supports_variable_sequence_lengths():
    import torch

    from symbolic_ir.mechinterp.patching import BatchPositionActivationPatcher

    class Tiny(torch.nn.Module):
        def __init__(self):
            super().__init__()
            self.block = torch.nn.Identity()

        def forward(self, value):
            return self.block(value)

    model = Tiny()
    recipient = torch.zeros(2, 5, 3)
    donors = [torch.ones(1, 3), torch.full((2, 3), 2.0)]
    with BatchPositionActivationPatcher(model, "block", donors, [[1], [2, 4]]):
        patched = model(recipient)
    assert torch.equal(patched[0, 1], torch.ones(3))
    assert torch.equal(patched[1, 2], torch.full((3,), 2.0))
    assert torch.equal(patched[1, 4], torch.full((3,), 2.0))
