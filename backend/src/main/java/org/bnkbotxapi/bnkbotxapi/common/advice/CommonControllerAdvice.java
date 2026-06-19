package org.bnkbotxapi.bnkbotxapi.common.advice;

import org.bnkbotxapi.bnkbotxapi.common.exception.CommonTaskException;
import org.springframework.http.ResponseEntity;
import org.springframework.web.bind.MethodArgumentNotValidException;
import org.springframework.web.bind.annotation.ExceptionHandler;
import org.springframework.web.bind.annotation.RestControllerAdvice;

import java.util.Map;

@RestControllerAdvice
public class CommonControllerAdvice {

    @ExceptionHandler(CommonTaskException.class)
    public ResponseEntity<Map<String, String>> handleTaskException(CommonTaskException e) {
        return ResponseEntity.status(e.getStatus())
                .body(Map.of("error", e.getCode(), "message", e.getMessage()));
    }

    @ExceptionHandler(MethodArgumentNotValidException.class)
    public ResponseEntity<Map<String, String>> handleValidation(MethodArgumentNotValidException e) {
        return ResponseEntity.badRequest()
                .body(Map.of("error", "VALIDATION_ERROR", "message", "Invalid request"));
    }
}
