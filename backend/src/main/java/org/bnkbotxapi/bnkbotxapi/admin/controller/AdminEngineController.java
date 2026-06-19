package org.bnkbotxapi.bnkbotxapi.admin.controller;

import lombok.RequiredArgsConstructor;
import org.bnkbotxapi.bnkbotxapi.engine.ChatbotEngineClient;
import org.bnkbotxapi.bnkbotxapi.engine.EngineManualDetailDTO;
import org.bnkbotxapi.bnkbotxapi.engine.EngineManualEditRequest;
import org.bnkbotxapi.bnkbotxapi.engine.EngineManualListResponse;
import org.bnkbotxapi.bnkbotxapi.manual.domain.ManualAuditEntity;
import org.bnkbotxapi.bnkbotxapi.manual.dto.ManualEditDTO;
import org.bnkbotxapi.bnkbotxapi.manual.repository.ManualAuditRepository;
import org.bnkbotxapi.bnkbotxapi.security.auth.CustomUserPrincipal;
import org.springframework.http.ResponseEntity;
import org.springframework.security.core.annotation.AuthenticationPrincipal;
import org.springframework.web.bind.annotation.*;

import java.util.Map;

@RestController
@RequestMapping("/api/v1/admin")
@RequiredArgsConstructor
public class AdminEngineController {

    private final ChatbotEngineClient engineClient;
    private final ManualAuditRepository manualAuditRepository;

    @GetMapping("engine/health")
    public ResponseEntity<Map<String, Object>> engineHealth() {
        return ResponseEntity.ok(engineClient.health());
    }

    @PostMapping("engine/ingest")
    public ResponseEntity<Map<String, Object>> ingest(@AuthenticationPrincipal CustomUserPrincipal principal) {
        Map<String, Object> result = engineClient.ingest();
        saveAudit("ENGINE_INGEST", null, principal);
        return ResponseEntity.ok(result);
    }

    @GetMapping("handoffs")
    public ResponseEntity<Map<String, Object>> handoffs(@RequestParam(required = false) String status) {
        return ResponseEntity.ok(engineClient.handoffs(status));
    }

    @PostMapping("handoffs/{handoffId}/resolve")
    public ResponseEntity<Map<String, Object>> resolveHandoff(
            @PathVariable Long handoffId,
            @AuthenticationPrincipal CustomUserPrincipal principal) {

        Map<String, Object> result = engineClient.resolveHandoff(handoffId);
        saveAudit("HANDOFF_RESOLVE", String.valueOf(handoffId), principal);
        return ResponseEntity.ok(result);
    }

    @GetMapping("manuals")
    public ResponseEntity<EngineManualListResponse> manuals() {
        return ResponseEntity.ok(engineClient.manuals());
    }

    @GetMapping("manuals/{manualId}")
    public ResponseEntity<EngineManualDetailDTO> manual(@PathVariable String manualId) {
        return ResponseEntity.ok(engineClient.manual(manualId));
    }

    @PutMapping("manuals/{manualId}")
    public ResponseEntity<Map<String, Object>> editManual(
            @PathVariable String manualId,
            @RequestBody ManualEditDTO body,
            @AuthenticationPrincipal CustomUserPrincipal principal) {

        Map<String, Object> result = engineClient.editManual(
                manualId,
                EngineManualEditRequest.builder()
                        .branchMd(body.getBranchMd())
                        .itMd(body.getItMd())
                        .by(principal.getUsername())
                        .build());
        saveAudit("MANUAL_EDIT", manualId, principal);
        return ResponseEntity.ok(result);
    }

    @PostMapping("manuals/{manualId}/approve")
    public ResponseEntity<Map<String, Object>> approveManual(
            @PathVariable String manualId,
            @AuthenticationPrincipal CustomUserPrincipal principal) {

        Map<String, Object> result = engineClient.approveManual(manualId, principal.getUsername());
        saveAudit("MANUAL_APPROVE", manualId, principal);
        return ResponseEntity.ok(result);
    }

    private void saveAudit(String actionType, String manualId, CustomUserPrincipal principal) {
        manualAuditRepository.save(ManualAuditEntity.builder()
                .manualId(manualId)
                .actionType(actionType)
                .actorId(principal.getAccountId())
                .actorLoginId(principal.getUsername())
                .build());
    }
}
